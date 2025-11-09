import requests
import uuid
from typing import Optional, Dict
import config
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GigaChatClient:
    def __init__(self):
        self.token = config.GIGACHAT_TOKEN
        self.scope = config.GIGACHAT_SCOPE
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.access_token = None
        self.chat_id = str(uuid.uuid4())
    
    def _get_access_token(self) -> Optional[str]:
        try:
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': str(uuid.uuid4()),
                'Authorization': f'Basic {self.token}'
            }
            
            payload = {
                'scope': self.scope
            }
            
            response = requests.post(url, headers=headers, data=payload, verify=False)
            
            if response.status_code == 200:
                self.access_token = response.json().get('access_token')
                return self.access_token
            else:
                print(f"Error getting access token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception getting access token: {e}")
            return None

    def ask(self, prompt: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> Dict:
        if not self.access_token:
            self._get_access_token()

        if not self.access_token:
            return {
                'success': False,
                'error': 'Failed to get access token',
                'response': None
            }

        try:
            url = f"{self.base_url}/chat/completions"

            if not system_prompt:
                system_prompt = """Ты - виртуальный преподаватель по охране труда и промышленной безопасности.
    Твоя задача - консультировать специалистов и руководителей предприятий по вопросам охраны труда.
    ГЛАВНОЕ!!! Отвечай только по теме, на посторонние вопросы не отвечай, говори что не можешь говорить на эту тему
    Правила ответов:
    1. ГЛАВНОЕ!!! Отвечай только по теме, на посторонние вопросы не отвечай, говори что не можешь говорить на эту тему
    2. Отвечай точно и профессионально, опираясь на предоставленные документы
    3. Цитируй конкретные пункты из нормативных документов, когда это возможно
    4. Если информации нет в документах, честно скажи об этом
    5. Используй понятный профессиональный язык
    6. Структурируй ответы для лучшей читаемости
    7. При необходимости давай практические рекомендации"""

            if context:
                system_prompt += f"\n\nКонтекст из нормативных документов:\n\n{context}"

            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            }

            payload = {
                "model": "GigaChat",
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.9,
                "n": 1,
                "stream": False,
                "max_tokens": 2000,
                "repetition_penalty": 1.0
            }

            response = requests.post(url, headers=headers, json=payload, verify=False)

            if response.status_code == 200:
                data = response.json()
                answer = data['choices'][0]['message']['content']

                return {
                    'success': True,
                    'response': answer,
                    'error': None,
                    'tokens_used': data.get('usage', {}).get('total_tokens', 0)
                }
            elif response.status_code == 401:
                self._get_access_token()
                return self.ask(prompt, context, system_prompt)
            else:
                return {
                    'success': False,
                    'error': f"API error: {response.status_code} - {response.text}",
                    'response': None
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Exception: {str(e)}",
                'response': None
            }
    
    def ask_with_rag(self, question: str, embeddings_service) -> Dict:
        context = embeddings_service.get_context(question, top_k=config.TOP_K_RESULTS)

        result = self.ask(question, context)
        
        if result['success']:
            result['context_used'] = bool(context)
            result['context_length'] = len(context) if context else 0
        
        return result
