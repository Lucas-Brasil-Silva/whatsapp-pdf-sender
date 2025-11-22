import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from gerenciador_csv import retornar_contato
import lista_pdfs

driver = None

def send_pdf(filepath: list, message: str = None, headless: bool = False, wait_time: int = 30, callback_log=None,callback_progress=None):
    global driver

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, wait_time)

    try:
        contatos = [retornar_contato(dado.split('-')[-1].replace('.pdf','')) for dado in filepath]
        nomes = [dado.split('-')[-1].replace('.pdf','') for dado in filepath]
        
        total_contatos = len(contatos)
        sucessos = 0
        erros = 0
        
        callback_log(f"Iniciando envio para {total_contatos} contatos.", "info") if total_contatos > 0 else callback_log(f"Sem PDF na pasta de envios.", "erro")
        
        for id, (contato, pdf)  in enumerate(zip(contatos, filepath)):
            
            if contato:
                
                callback_log(f"Enviando arquivo para o contato {nomes[id]}.", "info")

                try:
                    # Formatar o número de telefone para o formato internacional sem sinais
                    phone_digits = ''.join(c for c in contato if c.isdigit())
                    wa_url = f"https://web.whatsapp.com/send?phone={phone_digits}"
                    driver.get(wa_url)

                except Exception as e:
                    callback_log(f"Erro ao abrir o WhatsApp Web para {nomes[id]}: {e}", "erro")
                    continue

                # 1) Aguarda o carregamento do QR / autologin
                try:
                    callback_log("Aguardando login no WhatsApp Web (escaneie o QR se necessário)...", "aviso")
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id]/head/title")))
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='app']/div[1]/div/div[3]/div/header/div/div[2]/div/div[2]/span/button")))
                    callback_log("Login detectado ou sessão existente encontrada.", "sucesso")

                except TimeoutException:
                    callback_log("Não foi possível detectar o login automaticamente.", "erro")
                    callback_log("Por favor, escaneie o QR code no WhatsApp Web e pressione Enter para continuar...", "aviso")
                    input()

                # 2) Se a conversa ainda não estiver aberta, o parâmetro ?phone=... geralmente abre.
                # Aguarda o botão de anexar (clip) ou o campo de mensagem para saber que a conversa foi carregada.
                try:
                    attach_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='plus-rounded']")))
                except TimeoutException:
                    # alternativa: esperar area de input
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-tab][contenteditable='true']")))
                    attach_btn = driver.find_element(By.CSS_SELECTOR, "span[data-icon='plus-rounded']")

                # Clicar no clipe
                attach_btn.click()

                # O input[type=file] aparece na DOM; localizar e enviar o caminho do arquivo
                # Existem vários inputs; o primeiro input[type=file] é normalmente o de mídia
                time.sleep(0.5)
                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                if not file_inputs:
                    callback_log("Não foi possível anexar o arquivo no WhatsApp Web.", "erro")
                    continue

                # Enviar o arquivo via input
                file_input = file_inputs[0]
                file_input.send_keys(pdf)
                time.sleep(1)

                # Se houver mensagem, adicionar caption
                if message:
                    try:
                        # linhas = message.split("\n")
                        
                        caption_input = driver.find_element(By.XPATH, "//div[@contenteditable='true' and @aria-label='Digite uma mensagem']")
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
                        driver.execute_script(script_js,caption_input,message)
                        time.sleep(0.7)
        
                    except NoSuchElementException:
                        callback_log(f"Não foi possível enviar anexar a mensagem.", "erro")
                        continue

                # Aguarda aparecer preview e botão de enviar
                try:
                    send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @data-testid='send'] | //span[@data-icon='wds-ic-send-filled']")))
                except TimeoutException:
                    # Em alguns casos o botão tem outro seletor
                    callback_log("Não foi possível enviar realizar o envio.", "erro")
                    continue

                send_btn.click()

                # Pequena espera para garantir envio
                time.sleep(3)
                
                callback_log(f"Arquivo enviado para {nomes[id]}.", "sucesso")
                sucessos += 1
                callback_progress(total_contatos, sucessos, erros)
                lista_pdfs.mover_pdf(pdf.split('\\')[-1])

            else:
                callback_log(f"Contato não encontrado para o colaborador {nomes[id]}. Pulando envio.", "erro")
                erros += 1
                callback_progress(total_contatos, sucessos, erros)
   
    except Exception as e:
        callback_log(f"Erro geral durante o envio: {e}", "erro")
    
    finally:
        driver.quit()
        callback_log("Processo de envio concluído.", "info")

def fechar_driver():
    global driver

    if driver:
        try:
            driver.quit()
        except:
            pass
    driver = None
