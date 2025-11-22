import time
from pathlib import Path
from typing import List, Callable, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Importações dos seus módulos refatorados
from contatos import buscar_telefone
import file_organizer

class WhatsAppBot:
    SELECTORS = {
        'qr_canvas': "canvas",
        'main_page': "#pane-side",
        'attach_btn': "span[data-icon='plus-rounded'], div[title='Anexar']",
        'input_file': "input[type='file']",
        'msg_box': "div[contenteditable='true'][data-tab='10']",
        'send_btn': "span[data-icon='send'], span[data-icon='wds-ic-send-filled']"
    }

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.wait = None

    def _configurar_driver(self):
        """Configura o Chrome com perfil persistente para evitar QR Code toda vez."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        
        profile_path = Path.home() / "selenium_whatsapp_profile"
        options.add_argument(f"user-data-dir={profile_path}")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def iniciar(self, callback_log: Callable):
        """Inicia o browser e aguarda login."""
        if not self.driver:
            self._configurar_driver()
        
        callback_log("Abrindo WhatsApp Web...", "info")
        self.driver.get("https://web.whatsapp.com")
        
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.SELECTORS['main_page'])))
            callback_log("Login verificado com sucesso.", "sucesso")
        except TimeoutException:
            callback_log("Login automático falhou. Escaneie o QR Code.", "aviso")
            input("Pressione ENTER após escanear o QR Code...")

    def _inserir_mensagem_js(self, elemento, mensagem):
        """Hack JS para inserir texto com emojis e quebras de linha corretamente."""
        script_js = """
            var elm = arguments[0];
            var texto = arguments[1];
            elm.focus();
            var dataTransfer = new DataTransfer();
            dataTransfer.setData('text/plain', texto);
            var pasteEvent = new ClipboardEvent('paste', {
                clipboardData: dataTransfer,
                bubbles: true,
                cancelable: true
            });
            elm.dispatchEvent(pasteEvent);
        """
        self.driver.execute_script(script_js, elemento, mensagem)

    def enviar_arquivo(self, caminho_pdf: Path, telefone: str, mensagem: str = None) -> bool:
        """Lógica isolada de envio de UM arquivo."""

        try:
            phone_digits = ''.join(filter(str.isdigit, telefone))
            link = f"https://web.whatsapp.com/send?phone={phone_digits}"
            self.driver.get(link)

            attach_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.SELECTORS['attach_btn'])))
            
            attach_btn.click()
            time.sleep(0.5)
            
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, self.SELECTORS['input_file'])
            if not file_inputs:
                return False
            
            file_inputs[0].send_keys(str(caminho_pdf.absolute()))
            
            if mensagem:
                caption_box = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@contenteditable='true' and @aria-label='Digite uma mensagem']")
                ))
                time.sleep(0.5)
                self._inserir_mensagem_js(caption_box, mensagem)

            send_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.SELECTORS['send_btn'])))
            send_btn.click()
            
            time.sleep(3) 
            return True

        except Exception as e:
            print(f"Erro interno no envio: {e}")
            return False

    def fechar(self):
        if self.driver:
            self.driver.quit()

def processar_fila_envio(caminhos_arquivos: List[str], mensagem: str, callbacks):
    """
    Função wrapper para manter compatibilidade com sua interface gráfica.
    callbacks: tupla ou dict contendo (log_func, progress_func)
    """
    cb_log, cb_progresso = callbacks
    
    bot = WhatsAppBot(headless=False)
    
    try:
        bot.iniciar(cb_log)
        
        total = len(caminhos_arquivos)
        sucessos = 0
        erros = 0
        
        for i, caminho_str in enumerate(caminhos_arquivos):
            caminho = Path(caminho_str)
            nome_arquivo = caminho.name
            
            nome_colaborador = caminho.stem.split('-')[-1].strip()
            
            telefone = buscar_telefone(nome_colaborador)
            
            if not telefone:
                cb_log(f"Telefone não encontrado para: {nome_colaborador}", "erro")
                erros += 1
                cb_progresso(total, sucessos, erros)
                continue
            
            cb_log(f"Enviando para {nome_colaborador}...", "info")
            
            enviou = bot.enviar_arquivo(caminho, telefone, mensagem)
            
            if enviou:
                cb_log(f"Sucesso: {nome_arquivo}", "sucesso")
                sucessos += 1

                file_organizer.mover_pdf(nome_arquivo) 
            else:
                cb_log(f"Falha ao enviar: {nome_arquivo}", "erro")
                erros += 1
            
            cb_progresso(total, sucessos, erros)
            
    finally:
        bot.fechar()
        cb_log("Processo finalizado.", "info")