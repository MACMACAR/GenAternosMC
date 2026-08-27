import os
import time
import random
import json
import threading
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# ========== Flask для пинга ==========
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

flask_thread = threading.Thread(target=run_flask, daemon=True)
# ====================================

def setup_remote_driver():
    """Подключается к Selenium Standalone Chrome с автоопределением хоста"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Получаем хост из переменной окружения или пробуем стандартные имена
    host = os.environ.get('SELENIUM_HOST')
    if host:
        candidates = [host]
    else:
        candidates = ['selenium-standalone', 'selenium']  # порядок важен

    last_error = None
    for candidate in candidates:
        command_executor = f"http://{candidate}:4444/wd/hub"
        print(f'[GenAternosMC] Пробую подключиться к Selenium: {command_executor}')
        try:
            driver = webdriver.Remote(
                command_executor=command_executor,
                options=options
            )
            # Проверяем, что соединение установлено
            driver.get('about:blank')
            print(f'[GenAternosMC] Успешно подключено к {command_executor}')
            return driver
        except Exception as e:
            last_error = e
            print(f'[GenAternosMC] Ошибка подключения к {command_executor}: {e}')
            continue

    raise Exception(f'Не удалось подключиться ни к одному из хостов: {candidates}. Последняя ошибка: {last_error}')

def maintain_server_connection(driver):
    print('[GenAternosMC] Инициализация поддержания активности сервера')
    while True:
        try:
            extend_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@class="extend"]/button[@class="btn btn-tiny btn-success server-extend-end"]'))
            )
            extend_button.click()
            print('[GenAternosMC] Соединение с сервером продлено')
        except KeyboardInterrupt:
            print('[GenAternosMC] Получен сигнал прерывания (Ctrl+C)')
            break
        except Exception as e:
            try:
                timer_text = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="read-our-tos"]/main/section/div[3]/div[2]/div[1]/div/div/div[1]/div[1]/div'))
                ).text
                print(f'[GenAternosMC] Таймер: {timer_text}')
            except:
                pass
            handle_ad_popup(driver)
            time.sleep(random.randint(1, 7))

def handle_ad_popup(driver):
    try:
        ad_popup_button = driver.find_element(By.XPATH, '//div[contains(text(), "Всё равно продолжить с блокировщиком рекламы")]')
        ad_popup_button.click()
        time.sleep(4)
        return True
    except:
        return False

def show_logo():
    logo = """
   _____                    _                            __  __  _____ 
  / ____|              /\  | |                          |  \/  |/ ____|
 | |  __  ___ _ __    /  \ | |_ ___ _ __ _ __   ___  ___| \  / | |     
 | | |_ |/ _ \ '_ \  / /\ \| __/ _ \ '__| '_ \ / _ \/ __| |\/| | |     
 | |__| |  __/ | | |/ ____ \ ||  __/ |  | | | | (_) \__ \ |  | | |____ 
  \_____|\___|_| |_/_/    \_\__\___|_|  |_| |_|\___/|___/_|  |_|\_____|
    """
    print(logo)

def start_server(session_cookie, server_id, server_ip):
    driver = setup_remote_driver()
    try:
        print('[GenAternosMC] Remote драйвер подключен')
        time.sleep(3)
        driver.get('https://aternos.org/servers/')
        print('[GenAternosMC] Инициализация сервера...')
        driver.add_cookie({'name': 'ATERNOS_SESSION', 'value': session_cookie})
        driver.add_cookie({'name': "ATERNOS_SERVER", 'value': server_id})
        time.sleep(1)
        driver.get('https://aternos.org/server/')
        print('[GenAternosMC] Переход на страницу управления сервером')
        driver.refresh()
        handle_ad_popup(driver)
        driver.refresh()
        handle_ad_popup(driver)
        time.sleep(3)
        server_status_element = driver.find_element(By.XPATH,
                                                    '//*[@id="read-our-tos"]/main/section/div[3]/div[2]/div[1]/div/span[1]/span')
        server_status = server_status_element.text

        if "Оффлайн" in server_status:
            print('[GenAternosMC] Сервер оффлайн, пробуем запустить...')
            time.sleep(3)
            driver.find_element(By.XPATH, '//*[@id="start"]').click()
            print('[GenAternosMC] Сервер запускается...')
        elif 'Запуск' in server_status:
            time.sleep(3)
            print('[GenAternosMC] Сервер в процессе запуска...')
            time.sleep(35)
            if 'Онлайн' in driver.find_element(By.XPATH,
                                               '//*[@id="read-our-tos"]/main/section/div[3]/div[2]/div[1]/div/span[1]/span').text:
                print('[GenAternosMC] Сервер онлайн, поддержание соединения...')
                maintain_server_connection(driver)
        elif 'Онлайн' in server_status:
            print('[GenAternosMC] Сервер уже онлайн, поддержание соединения...')
            maintain_server_connection(driver)
    except KeyboardInterrupt:
        print('[GenAternosMC] Нажата комбинация CTRL+C, завершение...')
    except Exception as e:
        print(f'[GenAternosMC] Ошибка: {e}')
    finally:
        driver.quit()

if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    show_logo()
    print("""
╭──────────────────────────────────────────────────────╮
│ Использование: python GenAternosMC.py               │
│ (читает config.json)                                │
│ Переменная окружения SELENIUM_HOST (опционально)    │
╰──────────────────────────────────────────────────────╯
""")
    config_path = 'config.json'
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        ip_address = config['aternos_server']['ip']
        server_identifier = config['aternos_server']['server_id']
        session_id = config['aternos_server']['session_cookie']

    print(f'[GenAternosMC] Получен IP: {ip_address}')
    print(f'[GenAternosMC] Получен ID сервера: {server_identifier}')
    print(f'[GenAternosMC] Получена сессия: {session_id[:20]}...')

    # Запуск Flask
    flask_thread.start()
    print('[GenAternosMC] Flask-сервер запущен на порту 8080 для пинга')

    start_server(session_id, server_identifier, ip_address)
