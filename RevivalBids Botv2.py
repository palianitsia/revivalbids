import sys
import time
import random
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import os
import fake_useragent
import threading
import requests

class AuctionBot(QThread):
    update_status = pyqtSignal(str)
    update_data = pyqtSignal(int)
    update_history = pyqtSignal(str)
    update_balance = pyqtSignal(str)
    update_bid_used = pyqtSignal(str)
    
    def __init__(self, accounts, auction_id, bid_count, driver_path):
        super().__init__()
        self.accounts = accounts
        self.auction_id = auction_id
        self.bid_count = bid_count
        self.driver_path = driver_path
        self.driver = None
        self.running = True

    def run(self):
        user_agent = fake_useragent.UserAgent().random
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("tls-fingerprint=72:54:45:62:44:74:3f:60:24:53:7b:6e:58:73:22:7d:5c:7b:73:62")
        options.add_argument("http2-prior-knowledge")

        service = Service(self.driver_path)
        self.driver = webdriver.Chrome(service=service, options=options)
        
        self.inject_js()
        
        for account in self.accounts:
            self.login(account['username'], account['password'])
            self.navigate_to_auction(self.auction_id)
            if self.monitor_auction():
                break

    def inject_js(self):
        try:
            with open('C:\\Users\\Desktop\\RevivalBids\\detectIncognito669a.js', 'r') as file:
                detect_incognito_js = file.read()
            self.driver.execute_script(detect_incognito_js)
        except FileNotFoundError:
            print("Il file detectIncognito669a.js non è stato trovato nel percorso specificato.")
        except Exception as e:
            print(f"Si è verificato un errore durante la lettura del file: {e}")
        
        js_code = """
        function showProgressBar(txt, element, isNoBid){
            "use strict";
            element.hide();
            $(".auction-current-winner").show();
            var selector_timer = $(".auction-container-timer");
            selector_timer.removeClass("hidden");
            var bar = BidooCnf.instances.auction_progress;
            var wasStopped = bar.getStopCountDown();
            bar.setConfigurator(bar.getPreFilledConfiguration(Configurator.ids.SEMI_CIRCLE))
                .setContainer("#auction_timer"+(isSmartphoneDevice() ? "_mobile" : ""))
                .shouldUpdateTextAuto(false)
                .setBarColorThreshold(10)
                .stopTimer(false);
            if("object"==typeof txt){
                var data_price_winner = selector_timer.attr("data-price-winner");
                var current_price_winner = $(".auction-action-price strong").eq(0).text();
                var isNotAvailableWinner = "undefined"===typeof data_price_winner;
                var isDifferentWinner = isNotAvailableWinner || data_price_winner!=current_price_winner;
                
                var maxSeconds = parseInt($(".auction-action-timer > p > strong").html().split(" ")[0]);
                var shouldResetBar = isDifferentWinner;
                if(isDifferentWinner){
                    selector_timer.attr("data-price-winner",current_price_winner);
                }else{
                    var seconds = bar.getProgressSeconds();
                    bar.updateSecondsText(bar.getCorrectTimeMS(txt));
                    shouldResetBar = seconds<=bar.getProgressSeconds();
                }
                var shouldBlink = !isNotAvailableWinner && isDifferentWinner;
                if(shouldBlink) blinkEvent();
                if(shouldResetBar || wasStopped){
                    bar.resetBar(txt.getTime(),maxSeconds,200,shouldBlink || wasStopped,null,isNotAvailableWinner);
                }
                document.getElementsByClassName('text-countdown-progressbar')[0].classList.remove('text-arbitrary-progressbar-startstop');
            }else if("string"==typeof txt && !isSmartphoneDevice()){
                document.getElementsByClassName('text-countdown-progressbar')[0].classList.add('text-arbitrary-progressbar-startstop');
                bar.setArbitraryText(isTimerText ? window._controller.checkWinnerBid : txt);
            }
        }
        
        function isTimerText(txt){
            "use strict";
            return txt.split(":").length>1;
        }

        function setStatusBidButton(status, message, reason, additionalClass) {
            "use strict";
            var element = $(".auction-btn-bid").not("[disabled]");
            var defaults = "button-default button-rounded button-full ripple-button button-big-text auction-btn-bid";
            var mobileDefaults = ["btn btn-lg","auction-btn-bid","box_cards_button"];
            var base = "bid-button";
            var specific = '';
            switch(status) {
                case 'winning' : {
                    specific = "button-azure-flat";
                    element.off('click');
                    break;
                }
                case 'disabled-click':
                case 'disabled': {
                    specific = ["button-gray-flat",additionalClass || (isSmartphoneDevice() ? "button-sold-flat" : "")].join(" ");
                    if('disabled'==status) element.off('click');
                    $(".auction-swipeable-carousel .carousel-items").toggleClass("sold",true);
                    break;
                }
                case 'won': {
                    specific = "button-gold-flat";
                    element.off('click').on('click', function() {
                        if("function"==typeof reason) return reason();
                        window.parent.location.href = "/order_your_product.php?a=" + reason;
                    });
                    $(".auction-swipeable-carousel .carousel-items").toggleClass("sold",true);
                    break;
                }
                case 'login': {
                    specific = "button-mint-flat";
                    element.off('click').on('click', function(e) {
                        window.parent.showLogin();
                        rippleButton(element, e);
                    });
                    break;
                }
                case 'empty-soon':
                case 'empty': {
                    specific = [isSmartphoneDevice() ? "button-gray-flat" : "button-empty-flat",'empty-soon'==status ? "button-soon-empty-flat" : ""].join(" ");
                    element.off('click');
                    break;
                }
                case 'active':
                default: {
                    specific = "button-mint-flat";
                    element.off('click').on('click', function(e) {
                        window._controller.makeBid(0, 0);
                        rippleButton(element, e);
                    });
                    break;
                }
            }
        }

        function updateFunds(funds) {
            "use strict";
            if($("#divSaldoBidBottom").length > 0 || $("#divSaldoBidMobile").length > 0 || $("#divSaldoBidMobileRight").length > 0) {
                $("#divSaldoBidBottom").text(funds);
                $("#divSaldoBidMobile").text(funds);
                $("#divSaldoBidMobile", parent.document).text(funds);
                $("#divSaldoBidMobileRight").text(funds);
            }
        }

        function updateUserExpenditure(value) {
            "use strict";
            if($(".user-expenditure-value").length > 0) {
                var value = value > 0 ? value : 0;
                if(isSmartphoneDevice()){
                    $(".user-expenditure-value").text(value);
                    $(".auction-action-bid-mobile .buy-now-engage").toggle(value>0);
                }else{
                    $(".user-expenditure-value .expenditure-value").text(value);
                }
            }
        }

        function pushToBidHistory(element, price, type, typeColor, time, user, iE) {
            "use strict";
            if(iE !== false && iE < 9) {
                var newRow = element.insertRow(),
                td0 = newRow.insertCell(),
                td1 = newRow.insertCell(),
                td2 = newRow.insertCell(),
                td3 = newRow.insertCell();

                td0.innerHTML = price;
                td1.innerHTML = type;
                td2.innerHTML = time;
                td3.innerHTML = user;
            } else {
                $(element).append($("<tr><td class='hN'>" + (price || '&nbsp;') + "</td><td class='tB' style='color: "+typeColor+";'>" + (type || '&nbsp;') + "</td><td>" + (time || '&nbsp;') + "</td><td>" + (user || '&nbsp;') + "</td></tr>"));
            }
        }
        """
        self.driver.execute_script(js_code)

    def login(self, username, password):
        self.update_status.emit("Asta In Avvio")

        self.driver.get("https://it.bidoo.com")
        print("Pagina caricata: https://it.bidoo.com")

        self.simulate_mouse_movement(self.driver, self.driver.find_element(By.CSS_SELECTOR, 'body'))

        print("Attesa per il pulsante di login...")
        login_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, 'login_btn'))
        )
        self.simulate_human_click(self.driver, login_button)
        print("Pulsante di login cliccato")

        time.sleep(random.uniform(0.8, 1.2))

        print("Attesa per il campo email...")
        email_field = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input#field_email.email.form-control'))
        )
        self.simulate_human_typing(self.driver, email_field, username)
        print("Email inserita")

        print("Inserimento password...")
        password_field = self.driver.find_element(By.CSS_SELECTOR, 'input#password.pwd.form-control')
        self.simulate_human_typing(self.driver, password_field, password)
        print("Password inserita")

        print("Attesa per il pulsante ENTRA...")
        entra_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#logMeIn > div > div > div > div > div > form > div.login_submit_extra_area > button'))
        )
        self.simulate_human_click(self.driver, entra_button)
        print("Pulsante ENTRA cliccato")

        try:
            print("Attesa per il CAPTCHA...")
            captcha_frame = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[title="recaptcha challenge"]'))
            )
            QtWidgets.QMessageBox.information(None, "CAPTCHA", "CAPTCHA detected. Please solve it manually.")
            while True:
                try:
                    WebDriverWait(self.driver, 5).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[title="recaptcha challenge"]'))
                    )
                    break
                except:
                    continue
        except:
            print("No CAPTCHA detected")

        time.sleep(2)
        self.update_status.emit("Asta Attiva")
        self.get_balance()

    def navigate_to_auction(self, auction_id):
        self.driver.get(f"https://it.bidoo.com/auction.php?a={auction_id}")
        time.sleep(2)

    def get_logged_in_user(self, driver):
        url = "https://it.bidoo.com/ajax/get_logged_user.php"
        headers = {
            "User-Agent": driver.execute_script("return navigator.userAgent;"),
            "Cookie": "; ".join([f"{cookie['name']}={cookie['value']}"] for cookie in driver.get_cookies())
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            if user_data["is_valid"]:
                return user_data["username"]
            else:
                raise Exception("Utente non valido")
        else:
            raise Exception("Impossibile ottenere l'utente loggato")

    def monitor_auction(self):
        def find_timer():
            selectors = [
                (By.CSS_SELECTOR, 'div.text-countdown-progressbar'),
                (By.CSS_SELECTOR, 'div.auction-action-countdown div div'),
                (By.XPATH, f'//*[@id="{self.auction_id}"]/div[3]/section[1]/div/div[1]/section/div[1]/div/div'),
                (By.XPATH, f'/html/body/div[21]/div/div[3]/section[1]/div/div[1]/section/div[1]/div/div')
            ]
            for by, value in selectors:
                try:
                    timer = self.driver.find_element(by, value)
                    if timer:
                        return timer
                except:
                    continue
            raise Exception("Timer not found using any selector")

        def get_auction_history():
            selectors = [
                (By.XPATH, f'//*[@id="{self.auction_id}"]/div[3]/section[1]/div/section[3]'),
                (By.XPATH, f'/html/body/div[21]/div/div[3]/section[1]/div/section[3]')
            ]
            for by, value in selectors:
                try:
                    history = self.driver.find_element(by, value).get_attribute('innerHTML')
                    if history:
                        return history
                except:
                    continue
            return ""

        def check_auction_end():
            try:
                end_time_element = self.driver.find_element(By.XPATH, f'//*[@id="{self.auction_id}"]/div[3]/section[1]/div/section[1]/span[@data-closed-time]')
                if end_time_element:
                    return end_time_element.text
            except:
                return None

        def get_auction_winner():
            try:
                winner_element = self.driver.find_element(By.CSS_SELECTOR, f'#DA"{self.auction_id} > div.col-lg-5.col-md-5.col-sm-6.col-xs-12.action_auction > section.auction-action-container > div > div:nth-child(4) > div.auction-action-closed.hidden-xs > div.auction-closed-winner')
                if winner_element:
                    return winner_element.text
                return "Vincitore non trovato"
            except:
                return "Vincitore non trovato"

        def get_current_winner():
            try:
                current_winner_element = self.driver.find_element(By.CSS_SELECTOR, f'#DA"idasta" > div.col-lg-5.col-md-5.col-sm-6.col-xs-12.action_auction > section.auction-action-container > div > div.blink.background > section > div.auction-action-winner > p')
                if current_winner_element:
                    return current_winner_element.text
            except:
                return None

        def clicca_pulsante_punta(driver):
            try:
                punta_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#DA"idasta" > div.col-lg-5.col-md-5.col-sm-6.col-xs-12.action_auction > section.auction-action-container > div > section.auction-action-bid.hidden-xs.blink.background'))
                )
                time.sleep(random.uniform(0.01, 0.1))  # Aggiungi un piccolo ritardo casuale
                self.simulate_human_click(driver, punta_button)
            except Exception as e:
                print(f"Errore durante il tentativo di cliccare il bottone di puntata: {e}")

        def clicca_elemento_specifico(self):
            try:
                elemento = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f'#DA{idasta} > div.col-lg-5.col-md-5.col-sm-6.col-xs-12.product_details.hidden-xs > section.box.box-default.box-white.box-product > header > div.media-body > a'))
                )
                self.simulate_human_click(self.driver, elemento)
                print("Cliccato l'elemento specifico")
            except Exception as e:
                print(f"Errore durante il tentativo di cliccare l'elemento specifico: {e}")

        def inserisci_puntate(driver, numero_puntate):
            try:
                puntate_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#DA"idasta" > div.col-lg-5.col-md-5.col-sm-6.col-xs-12.action_auction > section.auction-action-container > div > section.auction-action-autobid.hidden-xs > main > section.form-inline.form-table > div:nth-child(1) > input'))
                )
                conferma_puntate_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#DA"idasta" > div.col-lg-5.col-md-5.col-sm-6.col-xs-12.action_auction > section.auction-action-container > div > section.auction-action-autobid.hidden-xs > main > section.form-inline.form-table > div:nth-child(2) > button'))
                )
                puntate_input.clear()
                puntate_input.send_keys(str(numero_puntate))
                time.sleep(random.uniform(0.01, 0.1))  # Aggiungi un piccolo ritardo casuale
                self.simulate_human_click(driver, conferma_puntate_button)
            except Exception as e:
                print(f"Errore durante l'inserimento delle puntate: {e}")

        last_second = 0
        consecutive_zero_seconds = 0
        logged_in_user = self.get_logged_in_user(self.driver)
        puntata_effettuata = False

        while self.running:
            try:
                timer = find_timer()
                timer_text = timer.text.strip()
                current_winner = get_current_winner()

                if current_winner and current_winner == logged_in_user:
                    print("L'utente loggato è l'attuale vincitore. Non verranno effettuate puntate.")
                    if puntata_effettuata:
                        self.clicca_elemento_specifico()
                        puntata_effettuata = False
                    continue

                if timer_text.isdigit():
                    total_seconds = int(timer_text)
                    print(f"Time left: {total_seconds} seconds")
                    if total_seconds == 1 and last_second != 0:
                        inserisci_puntate(self.driver, 5)
                        print("Inserite 5 puntate")
                        last_second = 0
                    elif total_seconds == 0:
                        clicca_pulsante_punta(self.driver)
                        print("Clicked the PUNTA button")
                        self.log_event("asta_log.txt", f"Puntata eseguita: {datetime.now()} - Sono la tua puntata")
                        self.bid_count -= 1
                        self.update_data.emit(self.bid_count)
                        puntata_effettuata = True
                        if self.bid_count <= 10 and len(self.accounts) > 1:
                            self.accounts.pop(0)
                            self.stop()
                            self.run()
                    else:
                        last_second = total_seconds

                    if total_seconds == 0:
                        consecutive_zero_seconds += 0.05
                        if consecutive_zero_seconds >= 2:
                            print("Timer stuck at zero. Starting rapid bid sequence.")
                            for _ in range(10):
                                try:
                                    clicca_pulsante_punta(self.driver)
                                    time.sleep(0.01)
                                except Exception as e:
                                    print(f"Errore durante il tentativo di cliccare il bottone di puntata: {e}")
                            consecutive_zero_seconds = 0
                    else:
                        consecutive_zero_seconds = 0
                else:
                    print(f"Timer text is not in the expected format: '{timer_text}'")

                auction_end_time = check_auction_end()
                if auction_end_time:
                    print(f"Asta finita alle {auction_end_time}")
                    winner = get_auction_winner()
                    print(f"Vincitore: {winner}")
                    self.update_status.emit("Asta Finita")
                    self.update_history.emit(f"L'asta è finita alle {auction_end_time}. Vincitore: {winner}")
                    break

                auction_history = get_auction_history()
                self.update_history.emit(auction_history)
                self.get_balance()
                self.get_bid_used()

            except Exception as e:
                print(f"Exception occurred: {e}")
                self.running = False  # Assicurati di fermare il ciclo in caso di errore
            time.sleep(0.1)

        return True

    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()

    def log_event(self, log_file, message):
        with open(log_file, "a") as file:
            file.write(f"{message}\n")

    def simulate_mouse_movement(self, driver, element):
        action = ActionChains(driver)
        action.move_to_element(element).perform()
        for _ in range(random.randint(5, 10)):
            action.move_by_offset(random.randint(-10, 10), random.randint(-10, 10)).perform()
            time.sleep(random.uniform(0.01, 0.5))
        action.move_to_element(element).perform()

    def simulate_human_click(self, driver, element):
        self.simulate_mouse_movement(driver, element)
        time.sleep(random.uniform(0.01, 0.06))
        element.click()

    def simulate_human_typing(self, driver, element, text):
        element.click()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
            if random.random() < 0.05:
                element.send_keys('\b')
                time.sleep(random.uniform(0.1, 0.3))
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

    def clicca_pulsante_punta(self, driver):
        punta_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.bid-button.button-default.button-rounded.button-full.ripple-button.button-big-text.auction-btn-bid.button-mint-flat.bid-button-active.hidden-xs'))
        )
        self.simulate_random_mouse_movement(driver, punta_button)
        self.simulate_human_click(driver, punta_button)

    def simulate_random_mouse_movement(self, driver, element):
        action = ActionChains(driver)
        start_element = driver.find_element(By.CSS_SELECTOR, 'body')
        action.move_to_element(start_element).perform()
        action.move_by_offset(random.randint(-100, 100), random.randint(-100, 100)).perform()
        action.move_to_element(element).perform()
        for _ in range(random.randint(5, 10)):
            action.move_by_offset(random.randint(-10, 10), random.randint(-10, 10)).perform()
            time.sleep(random.uniform(0.01, 0.5))
        action.move_to_element(element).perform()

    def get_balance(self):
        try:
            balance_element = self.driver.find_element(By.CSS_SELECTOR, 'span#divSaldoBidMobile')
            balance = balance_element.text
            self.update_balance.emit(balance)
        except:
            self.update_balance.emit("Saldo non trovato")

    def get_bid_used(self):
        try:
            bid_used_element = self.driver.find_element(By.CSS_SELECTOR, '#DA' + self.auction_id + ' > div.col-lg-5.col-md-5.col-sm-6.col-xs-12.product_details.hidden-xs > section.box.box-default.box-white.box-buynow.hidden-xs > main > div.buyitnow-status > p:nth-child(1) > span > span')
            bid_used = bid_used_element.text
            self.update_bid_used.emit(bid_used)
        except:
            self.update_bid_used.emit("Puntate usate non trovate")

class RevivalBidsGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.bots = []
        self.additional_accounts = []
        self.saved_accounts = []
        self.auction_running = False

    def init_ui(self):
        self.setWindowTitle("RevivalBids Bot")
        self.setGeometry(100, 100, 400, 700)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.96)
        self.setFixedSize(400, 700)
        self.setStyleSheet("background-color: rgb(221, 214, 195); font-family: 'Open Sans';")

        self.current_language = 'IT'
        self.translations = {
            'IT': {
                'title': "REVIVALBIDS",
                'options': "Opzioni",
                'username': "Username/Email",
                'show_username': "Mostra Username/Email",
                'password': "Password",
                'show_password': "Mostra Password",
                'auction_id': "ID Asta",
                'show_auction_id': "Nascondi ID Asta",
                'add_bids': "Aggiungi Puntate",
                'auto_update_bids': "Auto Aggiornamento (Scegli se aggiungi puntate extra)",
                'add_account': "Aggiungi Account",
                'save_accounts': "Salva Account",
                'start_auction': "Avvia Asta",
                'stop_auction': "Ferma Asta",
                'status': "Stato: Inattivo",
                'remaining_bids': "Puntate rimanenti: 0",
                'screenshot_saved': "Screenshot salvato nella directory corrente.",
                'error': "Errore",
                'fill_all_fields': "Tutti i campi devono essere compilati!",
                'auction_active': "Asta Attiva"
            },
            'EN': {
                'title': "REVIVALBIDS",
                'options': "Options",
                'username': "Username/Email",
                'show_username': "Show Username/Email",
                'password': "Password",
                'show_password': "Show Password",
                'auction_id': "Auction ID",
                'show_auction_id': "Hide Auction ID",
                'add_bids': "Add Bids",
                'auto_update_bids': "Auto Update (Choose if add extra bids)",
                'add_account': "Add Account",
                'save_accounts': "Save Accounts",
                'start_auction': "Start Auction",
                'stop_auction': "Stop Auction",
                'status': "Status: Inactive",
                'remaining_bids': "Remaining Bids: 0",
                'screenshot_saved': "Screenshot saved in current directory.",
                'error': "Error",
                'fill_all_fields': "All fields must be filled!",
                'auction_active': "Auction Active"
            },
            'UA': {
                'title': "REVIVALBIDS",
                'options': "Опції",
                'username': "Ім'я користувача/Електронна пошта",
                'show_username': "Показати ім'я користувача/Електронна пошта",
                'password': "Пароль",
                'show_password': "Показати пароль",
                'auction_id': "ID аукціону",
                'show_auction_id': "Приховати ID аукціону",
                'add_bids': "Додати ставки",
                'auto_update_bids': "Автоматичне оновлення (виберіть, якщо додати додаткові ставки)",
                'add_account': "Додати обліковий запис",
                'save_accounts': "Зберегти облікові записи",
                'start_auction': "Почати аукціон",
                'stop_auction': "Зупинити аукціон",
                'status': "Статус: Неактивний",
                'remaining_bids': "Залишилося ставок: 0",
                'screenshot_saved': "Знімок екрану збережено в поточному каталозі.",
                'error': "Помилка",
                'fill_all_fields': "Всі поля повинні бути заповнені!",
                'auction_active': "Аукціон активний"
            }
        }

        layout = QtWidgets.QVBoxLayout()

        title_label = QtWidgets.QLabel(self.translations[self.current_language]['title'], self)
        title_label.setFont(QtGui.QFont("Open Sans", 24, QtGui.QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.open_popup_button = QtWidgets.QPushButton(self.translations[self.current_language]['options'], self)
        self.open_popup_button.clicked.connect(self.show_popup)
        layout.addWidget(self.open_popup_button)

        self.username_input = QtWidgets.QLineEdit(self)
        self.username_input.setPlaceholderText(self.translations[self.current_language]['username'])
        layout.addWidget(self.username_input)

        self.show_username_var = QtWidgets.QCheckBox(self.translations[self.current_language]['show_username'], self)
        self.show_username_var.stateChanged.connect(self.toggle_show_username)
        layout.addWidget(self.show_username_var)

        self.password_input = QtWidgets.QLineEdit(self)
        self.password_input.setPlaceholderText(self.translations[self.current_language]['password'])
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.show_password_var = QtWidgets.QCheckBox(self.translations[self.current_language]['show_password'], self)
        self.show_password_var.stateChanged.connect(self.toggle_show_password)
        layout.addWidget(self.show_password_var)

        self.auction_id_input = QtWidgets.QLineEdit(self)
        self.auction_id_input.setPlaceholderText(self.translations[self.current_language]['auction_id'])
        layout.addWidget(self.auction_id_input)

        self.show_auction_id_var = QtWidgets.QCheckBox(self.translations[self.current_language]['show_auction_id'], self)
        self.show_auction_id_var.stateChanged.connect(self.toggle_show_auction_id)
        layout.addWidget(self.show_auction_id_var)

        self.bid_count_input = QtWidgets.QSpinBox(self)
        self.bid_count_input.setRange(1, 1000000)
        layout.addWidget(self.bid_count_input)

        self.add_bids_button = QtWidgets.QPushButton(self.translations[self.current_language]['add_bids'], self)
        self.add_bids_button.clicked.connect(self.add_bids)
        layout.addWidget(self.add_bids_button)

        self.auto_update_bids_var = QtWidgets.QCheckBox(self.translations[self.current_language]['auto_update_bids'], self)
        layout.addWidget(self.auto_update_bids_var)

        self.add_account_button = QtWidgets.QPushButton(self.translations[self.current_language]['add_account'], self)
        self.add_account_button.clicked.connect(self.add_account)
        layout.addWidget(self.add_account_button)

        self.save_accounts_button = QtWidgets.QPushButton(self.translations[self.current_language]['save_accounts'], self)
        self.save_accounts_button.clicked.connect(self.save_accounts)
        layout.addWidget(self.save_accounts_button)

        self.accounts_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.accounts_layout)

        self.start_stop_button = QtWidgets.QPushButton(self.translations[self.current_language]['start_auction'], self)
        self.start_stop_button.setStyleSheet("background-color: red")
        self.start_stop_button.clicked.connect(self.toggle_auction)
        layout.addWidget(self.start_stop_button)

        self.status_label = QtWidgets.QLabel(self.translations[self.current_language]['status'], self)
        layout.addWidget(self.status_label)

        self.bid_count_label = QtWidgets.QLabel(self.translations[self.current_language]['remaining_bids'], self)
        layout.addWidget(self.bid_count_label)

        self.tables_container = QtWidgets.QWidget(self)
        self.tables_container.setStyleSheet("background-color: rgba(221, 214, 195, 0.1); border: 0.5px solid rgba(43, 43, 43, 0.2);")
        self.tables_layout = QtWidgets.QHBoxLayout(self.tables_container)

        self.history_text_area = QtWidgets.QTextEdit(self.tables_container)
        self.history_text_area.setReadOnly(True)
        self.history_text_area.setMaximumWidth(int(self.width() * 0.7))
        self.tables_layout.addWidget(self.history_text_area)

        self.balance_text_area = QtWidgets.QTextEdit(self.tables_container)
        self.balance_text_area.setReadOnly(True)
        self.balance_text_area.setMaximumWidth(int(self.width() * 0.3))
        self.tables_layout.addWidget(self.balance_text_area)

        layout.addWidget(self.tables_container)

        self.history_overlay_text = QtWidgets.QLabel("dev by vmkhlv", self)
        self.history_overlay_text.setAlignment(Qt.AlignCenter)
        self.history_overlay_text.setStyleSheet("color: rgba(45, 45, 45, 0.9); font-size: 20px;")
        layout.addWidget(self.history_overlay_text)

        self.setLayout(layout)

    def show_popup(self):
        self.popup = QtWidgets.QDialog(self)
        self.popup.setWindowTitle(self.translations[self.current_language]['options'])

        layout = QtWidgets.QVBoxLayout()

        screenshot_button = QtWidgets.QPushButton("Effettua Screenshot", self.popup)
        screenshot_button.clicked.connect(self.take_screenshot)
        layout.addWidget(screenshot_button)

        language_label = QtWidgets.QLabel("Seleziona Lingua:", self.popup)
        layout.addWidget(language_label)

        self.language_combo = QtWidgets.QComboBox(self.popup)
        self.language_combo.addItem("IT")
        self.language_combo.addItem("EN")
        self.language_combo.addItem("UA")
        self.language_combo.currentIndexChanged.connect(self.change_language)
        layout.addWidget(self.language_combo)

        self.popup.setLayout(layout)
        self.popup.exec_()

    def open_new_bot_window(self):
        new_window = RevivalBidsGUI()
        new_window.show()

    def take_screenshot(self):
        screen = QtWidgets.QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        screenshot.save(os.path.join(os.getcwd(), 'screenshot.png'), 'png')
        QtWidgets.QMessageBox.information(self, self.translations[self.current_language]['screenshot_saved'], self.translations[self.current_language]['screenshot_saved'])

    def set_icon(self, icon_path):
        app_icon = QtGui.QIcon(icon_path)
        self.setWindowIcon(app_icon)

    def toggle_show_username(self):
        if self.show_username_var.isChecked():
            self.username_input.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.username_input.setEchoMode(QtWidgets.QLineEdit.Password)

    def toggle_show_password(self):
        if self.show_password_var.isChecked():
            self.password_input.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)

    def toggle_show_auction_id(self):
        if self.show_auction_id_var.isChecked():
            self.auction_id_input.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.auction_id_input.setEchoMode(QtWidgets.QLineEdit.Password)

    def add_bids(self):
        additional_bids = self.bid_count_input.value()
        for bot in self.bots:
            bot.bid_count += additional_bids
        self.update_bid_count_label()

    def add_account(self):
        account_widget = QtWidgets.QWidget()
        account_layout = QtWidgets.QHBoxLayout()

        email_input = QtWidgets.QLineEdit(self)
        email_input.setPlaceholderText(self.translations[self.current_language]['username'])
        account_layout.addWidget(email_input)

        password_input = QtWidgets.QLineEdit(self)
        password_input.setPlaceholderText(self.translations[self.current_language]['password'])
        password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        account_layout.addWidget(password_input)

        remove_button = QtWidgets.QPushButton("Rimuovi", self)
        remove_button.clicked.connect(lambda: self.remove_account(account_widget))
        account_layout.addWidget(remove_button)

        account_widget.setLayout(account_layout)
        self.accounts_layout.addWidget(account_widget)
        self.additional_accounts.append({'email': email_input, 'password': password_input})

    def save_accounts(self):
        self.saved_accounts = [{'email': acc['email'].text(), 'password': acc['password'].text()} for acc in self.additional_accounts]
        QtWidgets.QMessageBox.information(self, self.translations[self.current_language]['save_accounts'], self.translations[self.current_language]['save_accounts'])

    def remove_account(self, account_widget):
        self.accounts_layout.removeWidget(account_widget)
        account_widget.setParent(None)
        account_widget.deleteLater()
        self.additional_accounts = [acc for acc in self.additional_accounts if acc['email'] != account_widget]

    def toggle_auction(self):
        if not self.auction_running:
            if not self.username_input.text() or not self.password_input.text() or not self.auction_id_input.text() or self.bid_count_input.value() == 0:
                QtWidgets.QMessageBox.warning(self, self.translations[self.current_language]['error'], self.translations[self.current_language]['fill_all_fields'])
                return
            self.start_auction()
        else:
            self.stop_auction()

    def start_auction(self):
        accounts = [{'username': self.username_input.text(), 'password': self.password_input.text()}]
        for acc in self.additional_accounts:
            accounts.append({'username': acc['email'].text(), 'password': acc['password'].text()})

        auction_id = self.auction_id_input.text()
        bid_count = self.bid_count_input.value()

        bot = AuctionBot(accounts, auction_id, bid_count, "C:\\Users\\Desktop\\RevivalBids\\chromedriver.exe")
        bot.update_status.connect(self.update_status)
        bot.update_data.connect(self.update_bid_count_label)
        bot.update_history.connect(self.update_history_text_area)
        bot.update_balance.connect(self.update_balance_text_area)
        bot.update_bid_used.connect(self.update_bid_used_text_area)
        self.bots.append(bot)
        bot.start()

        self.auction_running = True
        self.start_stop_button.setText(self.translations[self.current_language]['stop_auction'])
        self.start_stop_button.setStyleSheet("background-color: yellow")

    def stop_auction(self):
        for bot in self.bots:
            bot.stop()
        self.bots = []

        self.auction_running = False
        self.status_label.setText(self.translations[self.current_language]['status'])
        self.start_stop_button.setText(self.translations[self.current_language]['start_auction'])
        self.start_stop_button.setStyleSheet("background-color: red")

    def update_status(self, status):
        self.status_label.setText(f"{self.translations[self.current_language]['status'].split(':')[0]}: {status}")
        if status == self.translations[self.current_language]['auction_active']:
            self.start_stop_button.setText(self.translations[self.current_language]['stop_auction'])
            self.start_stop_button.setStyleSheet("background-color: yellow")

    def update_bid_count_label(self, bid_count=None):
        if bid_count is not None:
            self.bid_count_label.setText(f"{self.translations[self.current_language]['remaining_bids'].split(':')[0]}: {bid_count}")
        else:
            total_bids = sum(bot.bid_count for bot in self.bots)
            self.bid_count_label.setText(f"{self.translations[self.current_language]['remaining_bids'].split(':')[0]}: {total_bids}")

    def update_history_text_area(self, history):
        self.history_text_area.setHtml(history)

    def update_balance_text_area(self, balance):
        self.balance_text_area.setHtml(f"Saldo: {balance}")

    def update_bid_used_text_area(self, bid_used):
        self.balance_text_area.append(f"Puntate usate: {bid_used}")

    def change_language(self):
        self.current_language = self.language_combo.currentText()
        self.update_ui_texts()

    def update_ui_texts(self):
        self.setWindowTitle(self.translations[self.current_language]['title'])
        self.open_popup_button.setText(self.translations[self.current_language]['options'])
        self.username_input.setPlaceholderText(self.translations[self.current_language]['username'])
        self.show_username_var.setText(self.translations[self.current_language]['show_username'])
        self.password_input.setPlaceholderText(self.translations[self.current_language]['password'])
        self.show_password_var.setText(self.translations[self.current_language]['show_password'])
        self.auction_id_input.setPlaceholderText(self.translations[self.current_language]['auction_id'])
        self.show_auction_id_var.setText(self.translations[self.current_language]['show_auction_id'])
        self.add_bids_button.setText(self.translations[self.current_language]['add_bids'])
        self.auto_update_bids_var.setText(self.translations[self.current_language]['auto_update_bids'])
        self.add_account_button.setText(self.translations[self.current_language]['add_account'])
        self.save_accounts_button.setText(self.translations[self.current_language]['save_accounts'])
        self.start_stop_button.setText(self.translations[self.current_language]['start_auction'] if not self.auction_running else self.translations[self.current_language]['stop_auction'])
        self.status_label.setText(self.translations[self.current_language]['status'])
        self.bid_count_label.setText(self.translations[self.current_language]['remaining_bids'])

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = RevivalBidsGUI()
    icon_path = os.path.join(os.getcwd(), 'pictures', 'icon.png')
    window.set_icon(icon_path)
    window.show()
    sys.exit(app.exec_())
