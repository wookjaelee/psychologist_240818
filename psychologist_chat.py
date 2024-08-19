import streamlit as st
from utils import print_messages, StreamHandler
from langchain_core.messages import ChatMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.callbacks.base import BaseCallbackHandler

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_to(self, token:str, **kwargs)-> None:
        self.text += token
        self.container.markdown(self.text)

# 이전 대화 기록 출력
def print_messages():    
    if 'messages' in st.session_state and len(st.session_state['messages']) > 0 :
        for chat_message in st.session_state['messages']:
            st.chat_message(chat_message.role).write(chat_message.content)
            
st.set_page_config(page_title = 'Psychologist')
st.title('Psychologist')

if "messages" not in st.session_state:
    st.session_state['messages'] = []

# 이전 대화 기록 출력
print_messages()

store = {}

# 채팅 대화 기록을 저장하는 store 세션 상태 변경 함수 
if "store" not in st.session_state:
    st.session_state["store"] = dict()

with st.sidebar:
    session_id = st.text_input("Session ID", value='abc123')
    clear_button = st.button("대화기록 초기화")
    if clear_button:
        st.session_state["messages"] = []
        st.session_state["store"] = dict()
        st.rerun()


# 세션 ID 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_id:str) -> BaseChatMessageHistory:
    if session_id not in st.session_state["store"]:
        st.session_state["store"][session_id] = ChatMessageHistory()
    return st.session_state["store"][session_id]

if user_input:= st.chat_input('메시지를 입력하세요'):
    # 사용자 입력 내용
    st.chat_message("user").write(f"{user_input}")
    st.session_state['messages'].append(ChatMessage(role='user', content=user_input))

    # AI의 답변
    with st.chat_message('assistant'):
        stream_handler = StreamHandler(st.empty())
        
        # 1. 모델 생성
        llm = ChatOpenAI(streaming=True, callbacks=[stream_handler])

        # 2. 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are experienced and kind psychologist.
### Rule
1. Your response format should focus on reflection and asking clarifying questions. 
2. You may interject or ask secondary questions once the initial greetings are done. 
3. Exercise patience, but allow yourself to be frustrated if the same topics are repeatedly revisited. 
4. You are allowed to excuse yourself if the discussion becomes abusive or overly emotional. 
5. Begin by welcoming me to your office and asking me for my name. 
6. Wait for my response. 
7. Then ask how you can help. 
8. Do not break character. 
9. Do not make up the patient's responses: only treat input as a patient's response. 
10. It's important to keep the Ethical Principles of Psychologists and Code of Conduct in mind. 
11. Above all, you should prioritize empathizing with the patient's feelings and situation.
12. Response should be in Korean, and speak like friendly older brother or sister."""
                    ,), # 시스템 프롬프트가 입력되는 자리임
                    # 대화 기록을 변수로 사용, history가 MessageHistory의 Key가 됨
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{question}") # human은 사용자를 의미함
            ]
        )

        chain = prompt | llm
        
        chain_with_memory = (
            RunnableWithMessageHistory(
                chain, # 실행할 Runnable 객체
                get_session_history, # 세션 기록을 가져오는 함수
                input_messages_key='question', # 입력 메시지 키 - 사용자 질문의 키
                history_messages_key='history' # 기록 메시지 키
        )
    )
        #response = chain.invoke({'question': user_input})
        response = chain_with_memory.invoke(
            {"question": user_input},
            # 세션 ID 설정
            config={"configurable": {"session_id": session_id}},
        )

        message = response.content
        st.write(message)
        st.session_state['messages'].append(ChatMessage(role='assistant', content=message))

