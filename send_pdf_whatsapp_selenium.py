import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from gerenciador_csv import retornar_contato
import lista_pdfs

def send_pdf(filepath: list, message: str = None, headless: bool = False, wait_time: int = 30, callback_log=None,callback_progress=None):

    # service = Service(ChromeDriverManager().install())
    # driver = webdriver.Chrome(service=service)
    # wait = WebDriverWait(driver, wait_time)

    try:
        contatos = [retornar_contato(dado.split('-')[-1].replace('.pdf','')) for dado in filepath]
        nomes = [dado.split('-')[-1].replace('.pdf','') for dado in filepath]
        total_contatos = len(contatos)
        sucessos = 0
        erros = 0
        callback_log(f"Iniciando envio para {total_contatos} contatos.", "info")
        for id, (contato, pdf)  in enumerate(zip(contatos, filepath)):
            if contato:  # Se o telefone foi encontrado
                
                callback_log(f"Enviando arquivo para o contato {nomes[id]}.", "info")
                time.sleep(0.5)  # Simula tempo de envio
                callback_log(f"Arquivo enviado para {nomes[id]}.", "sucesso")
                sucessos += 1
                callback_progress(total_contatos, sucessos, erros)

                # phone_digits = ''.join(c for c in contato if c.isdigit())
                # wa_url = f"https://web.whatsapp.com/send?phone={phone_digits}"
                # driver.get(wa_url)

                # # 1) Aguarda o carregamento do QR / autologin
                # try:
                #     print("Aguardando login no WhatsApp Web (escaneie o QR se necessário)...")
                #     # exemplo: esperar elemento do search box que aparece quando está logado
                #     wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id]/head/title")))
                #     wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='app']/div[1]/div/div[3]/div/header/div/div[2]/div/div[2]/span/button")))
                #     print("Login detectado ou sessão existente encontrada.")

                # except TimeoutException:
                #     # É possível que a página ainda precise de mais tempo; pedir usuário
                #     print("Tempo esgotado aguardando login. Certifique-se de escanear o QR e pressione Enter para continuar...")
                #     input()

                # # 2) Se a conversa ainda não estiver aberta, o parâmetro ?phone=... geralmente abre.
                # # Aguarda o botão de anexar (clip) ou o campo de mensagem para saber que a conversa foi carregada.
                # try:
                #     attach_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='plus-rounded']")))
                # except TimeoutException:
                #     # alternativa: esperar area de input
                #     wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-tab][contenteditable='true']")))
                #     attach_btn = driver.find_element(By.CSS_SELECTOR, "span[data-icon='plus-rounded']")

                # # Clicar no clipe
                # attach_btn.click()

                # # O input[type=file] aparece na DOM; localizar e enviar o caminho do arquivo
                # # Existem vários inputs; o primeiro input[type=file] é normalmente o de mídia
                # time.sleep(0.5)
                # file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                # if not file_inputs:
                #     raise RuntimeError("Não foi possível encontrar o input de arquivo no WhatsApp Web.")

                # # Enviar o arquivo via input
                # file_input = file_inputs[0]
                # print(f"Anexando arquivo: {pdf}")
                # file_input.send_keys(pdf)
                # time.sleep(1)

                # # Se houver mensagem, adicionar caption
                # if message:
                #     try:
                #         # Procurar pelo input de caption que aparece após anexar arquivo
                #         caption_input = driver.find_element(By.XPATH, "//div[@contenteditable='true' and @aria-label='Digite uma mensagem']") 
                #         caption_input.click()
                #         caption_input.send_keys(message)
                #     except NoSuchElementException:
                #         # Se não encontrar o input de caption, pular
                #         print(f"Não foi possível adicionar caption, enviando apenas com arquivo.")

                # # Aguarda aparecer preview e botão de enviar
                # try:
                #     send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @data-testid='send'] | //span[@data-icon='wds-ic-send-filled']")))
                # except TimeoutException:
                #     # Em alguns casos o botão tem outro seletor
                #     time.sleep(2)
                #     send_btn = driver.find_element(By.XPATH, "//span[@data-icon='wds-ic-send-filled']")

                # print("Enviando arquivo...")
                # send_btn.click()

                # # Pequena espera para garantir envio
                # time.sleep(3)
                # print("Arquivo enviado (ou pedido de envio efetuado). Verifique o chat no WhatsApp Web.")
            else:
                callback_log(f"Contato não encontrado para o colaborador {nomes[id]}. Pulando envio.", "erro")
                erros += 1
                callback_progress(total_contatos, sucessos, erros)
    except Exception as e:
        print(f"Erro durante o envio: {e}")

def main():
    mensagem = "Olá, esse arquivo foi enviado via script Python usando Selenium."
    send_pdf(filepath=lista_pdfs.listar_pdfs_na_pasta(), message=mensagem)
    print("Processo concluído.")
    # try:
        
    # except Exception as e:
    #     print(f"Erro: {e}")
    #     sys.exit(1)


if __name__ == '__main__':
    main()
