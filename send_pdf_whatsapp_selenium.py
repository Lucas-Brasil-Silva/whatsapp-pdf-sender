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


def send_pdf(phones: list, filepath: str, message: str = None, headless: bool = False, wait_time: int = 30):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, wait_time)

    try:
        # Abrir WhatsApp Web na conversa do número
        for phone  in phones:
            phone_digits = ''.join(c for c in phone if c.isdigit())
            wa_url = f"https://web.whatsapp.com/send?phone={phone_digits}"
            driver.get(wa_url)

            # 1) Aguarda o carregamento do QR / autologin
            try:
                print("Aguardando login no WhatsApp Web (escaneie o QR se necessário)...")
                # exemplo: esperar elemento do search box que aparece quando está logado
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id]/head/title")))
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='app']/div[1]/div/div[3]/div/header/div/div[2]/div/div[2]/span/button")))
                print("Login detectado ou sessão existente encontrada.")

            except TimeoutException:
                # É possível que a página ainda precise de mais tempo; pedir usuário
                print("Tempo esgotado aguardando login. Certifique-se de escanear o QR e pressione Enter para continuar...")
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
                raise RuntimeError("Não foi possível encontrar o input de arquivo no WhatsApp Web.")

            # Enviar o arquivo via input
            file_input = file_inputs[0]
            abs_path = os.path.abspath(filepath)
            print(f"Anexando arquivo: {abs_path}")
            file_input.send_keys(abs_path)
            time.sleep(1)

            # Se houver mensagem, adicionar caption
            if message:
                try:
                    # Procurar pelo input de caption que aparece após anexar arquivo
                    caption_input = driver.find_element(By.XPATH, "//div[@contenteditable='true' and @aria-label='Digite uma mensagem']") 
                    caption_input.click()
                    caption_input.send_keys(message)
                except NoSuchElementException:
                    # Se não encontrar o input de caption, pular
                    print(f"Não foi possível adicionar caption, enviando apenas com arquivo.")

            # Aguarda aparecer preview e botão de enviar
            try:
                send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @data-testid='send'] | //span[@data-icon='wds-ic-send-filled']")))
            except TimeoutException:
                # Em alguns casos o botão tem outro seletor
                time.sleep(2)
                send_btn = driver.find_element(By.XPATH, "//span[@data-icon='wds-ic-send-filled']")

            print("Enviando arquivo...")
            send_btn.click()

            # Pequena espera para garantir envio
            time.sleep(3)
            print("Arquivo enviado (ou pedido de envio efetuado). Verifique o chat no WhatsApp Web.")
    
    except Exception as e:
        print(f"Erro durante o envio: {e}")

def main():
    lista_phone = []
    mensagem = "Olá, esse arquivo foi enviado via script Python usando Selenium."

    try:
        send_pdf(phones=lista_phone, filepath="Modelo de Holerite.pdf", message=mensagem)
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
