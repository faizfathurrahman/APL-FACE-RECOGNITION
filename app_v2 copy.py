import cv2
import sqlite3
from datetime import datetime
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFormLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox, QDialog, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFormLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox, QDialog, QSpacerItem, QSizePolicy,
    QGridLayout  # Add this line
)
from PyQt6.QtCore import QSize
import numpy as np
import shutil
import sys
import traceback

# Database setup
conn = sqlite3.connect('face_detection.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS biodata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nim TEXT,
    nama TEXT,
    alamat TEXT,
    hp TEXT,
    email TEXT,
    username TEXT,
    password TEXT,
    role TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT,
    nim TEXT,
    nama TEXT
)
''')
conn.commit()

# Menambahkan kolom username, password, dan role ke tabel biodata
try:
    cursor.execute("ALTER TABLE biodata ADD COLUMN username TEXT")
    cursor.execute("ALTER TABLE biodata ADD COLUMN password TEXT")
    cursor.execute("ALTER TABLE biodata ADD COLUMN role TEXT")
    conn.commit()
    print("Kolom berhasil ditambahkan.")
except sqlite3.OperationalError as e:
    print(f"Kesalahan: {e}")

# Menutup koneksi
conn.close()

class FaceDetectionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Detection System")
        self.setFixedSize(600, 400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Inisialisasi camera_label dan user_data_label sebagai None
        self.camera_label = None
        self.user_data_label = None

        self.show_main_menu()

    def show_main_menu(self):
        self.clear_layout()

        # Title for the login form
        title_label = QLabel("Login to Face Detection System")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")  # Placeholder text
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")  # Placeholder text

        btn_login = QPushButton("Login")
        btn_login.clicked.connect(self.login)

        # Adding spacing for better layout
        self.layout.addWidget(QLabel("Username:"))
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(QLabel("Password:"))
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(btn_login)

        # Adding some spacing at the bottom
        self.layout.addStretch()

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Membuka koneksi ke database
        conn = sqlite3.connect('face_detection.db')
        cursor = conn.cursor()

        try:
            if username == "admin" and password == "admin":
                self.show_admin_mode()
            else:
                # Melakukan operasi SELECT untuk login
                cursor.execute("SELECT * FROM biodata WHERE username = ? AND password = ?", (username, password))
                user = cursor.fetchone()  # Mengambil satu data pengguna
                if user:
                    print(f"Login berhasil! Selamat datang, {user[2]}!")  # Misalnya user[2] adalah nama
                    self.show_user_dashboard(user)
                else:
                    print("Username atau password salah!")
        except sqlite3.Error as e:
            print(f"Kesalahan saat melakukan login: {e}")
        finally:
            # Menutup koneksi
            cursor.close()
            conn.close()

    def show_user_dashboard(self, user):
        self.clear_layout()
        self.clear_user_data()  # Panggil untuk menghapus gambar dan biodata

        self.layout.addWidget(QLabel(f"Selamat datang, {user[2]}!"))  # Assuming user[2] is the name
        self.absen_button = QPushButton("Absen")  # Simpan referensi ke tombol Absen
        self.absen_button.clicked.connect(lambda: self.absen(user))  # Pass the entire user object
        self.layout.addWidget(self.absen_button)

        # Tombol Logout
        self.logout_button = QPushButton("Logout")  # Simpan referensi ke tombol Logout
        self.logout_button.clicked.connect(self.logout)
        self.layout.addWidget(self.logout_button)

    def logout(self):
        # Periksa apakah camera_label dan user_data_label tidak None sebelum menghapus
        if self.camera_label:
            print("Menghapus camera_label...")
            self.camera_label.clear()  # Clear camera label
            self.camera_label.deleteLater()  # Menghapus widget dari memori
            self.camera_label = None  # Set ke None setelah dihapus

        if self.user_data_label:
            print("Menghapus user_data_label...")
            self.user_data_label.clear()  # Clear user data label
            self.user_data_label.deleteLater()  # Menghapus widget dari memori
            self.user_data_label = None  # Set ke None setelah dihapus
        
        self.show_main_menu()  # Kembali ke menu utama

    def absen(self, user):
        self.clear_layout()  # Hapus semua widget dari layout

        # Menyiapkan layout horizontal untuk gambar dan biodata
        h_layout = QHBoxLayout()

        # Membuat kembali camera_label dan user_data_label
        self.camera_label = QLabel(self)
        self.camera_label.setFixedSize(375, 330)  # Atur ukuran gambar
        self.camera_label.setScaledContents(True)  # Agar gambar menyesuaikan ukuran label
        h_layout.addWidget(self.camera_label)

        self.user_data_label = QLabel(self)
        self.user_data_label.setFixedSize(180, 180)  # Atur ukuran
        self.user_data_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Rata kiri
        h_layout.addWidget(self.user_data_label)

        self.layout.addLayout(h_layout)

        # Tombol Kembali
        btn_back = QPushButton("Kembali")
        btn_back.clicked.connect(lambda: self.back_to_dashboard(user))
        self.layout.addWidget(btn_back)

        # Sembunyikan tombol Logout dan Absen
        self.logout_button.setVisible(False)  # Sembunyikan tombol Logout
        self.absen_button.setVisible(False)  # Sembunyikan tombol Absen

        # Mulai kamera dan tampilkan gambar
        self.start_camera(user)

        # Tambahkan riwayat absensi ke database
        self.add_absence_to_history(user)

    def add_absence_to_history(self, user):
        tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nim = user[1]  # Ambil NIM dari objek user
        nama = user[2]  # Ambil nama dari objek user

        # Membuka koneksi ke database
        conn = sqlite3.connect('face_detection.db')
        cursor = conn.cursor()

        try:
            # Menambahkan data absensi ke tabel history
            cursor.execute("INSERT INTO history (tanggal, nim, nama) VALUES (?, ?, ?)", (tanggal, nim, nama))
            conn.commit()  # Simpan perubahan
            print(f"Absensi berhasil ditambahkan: Tanggal: {tanggal}, NIM: {nim}, Nama: {nama}")
        except sqlite3.Error as e:
            print(f"Kesalahan saat menambahkan absensi: {e}")
        finally:
            cursor.close()
            conn.close()
    def clear_layout(self):
        # Remove and delete all widgets in the layout
        while self.layout.count():
            # Get the first item in the layout
            item = self.layout.takeAt(0)
            
            # If it's a widget, delete it
            if item.widget():
                widget = item.widget()
                widget.deleteLater()
            
            # If it's a layout, clear that layout as well
            elif item.layout():
                sub_layout = item.layout()
                # Clear the sub-layout recursively
                while sub_layout.count():
                    sub_item = sub_layout.takeAt(0)
                    if sub_item.widget():
                        sub_widget = sub_item.widget()
                        sub_widget.deleteLater()
        
        # Reset the layout to ensure it's completely clear
        self.layout.update()

    def back_to_dashboard(self, user):
        self.clear_user_data()  # Hapus gambar dan biodata
        self.show_user_dashboard(user)  # Tampilkan kembali dashboard pengguna

    def start_camera(self, user):
        cap = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        print("Mulai scanning wajah...")
        count = 0
        is_absent = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                count += 1
                face_image = gray[y:y+h, x:x+w]
                face_image = cv2.resize(face_image, (100, 100))

                # Tampilkan gambar wajah di camera_label
                self.show_camera_image(frame)

                if count >= 30:
                    break

            if count >= 30 or is_absent:
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        # Tampilkan biodata setelah kamera selesai
        self.user_data_label.setText(f"<b>Nama:</b> {user[2]}<br>"
                                      f"<b>NIM:</b> {user[1]}<br>"
                                      f"<b>Alamat:</b> {user[3]}<br>"
                                      f"<b>HP:</b> {user[4]}<br>"
                                      f"<b>Email:</b> {user[5]}")

    def show_camera_image(self, img):
        # Convert and display the image in the QLabel
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(q_img))

    def show_admin_mode(self):
        # Hapus semua widget dan layout yang ada sebelumnya
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    sub_layout = item.layout()
                    if sub_layout is not None:
                        clear_layout(sub_layout)

        clear_layout(self.layout)

        # Membuat layout grid untuk posisi yang lebih fleksibel
        grid_layout = QGridLayout()

        # Membuat tombol gambar
        btn_add_user = QPushButton()
        btn_view_users = QPushButton()
        btn_view_history = QPushButton()
        btn_logout = QPushButton()

        # Load gambar untuk tombol
        pixmap_add_user = QPixmap("logo.png")  # Ganti dengan path gambar sebenarnya
        pixmap_view_users = QPixmap("logo.png")
        pixmap_view_history = QPixmap("logo.png")
        pixmap_logout = QPixmap("logo.png")

        # Membuat label untuk menampilkan gambar
        label_add_user = QLabel()
        label_view_users = QLabel()
        label_view_history = QLabel()
        label_logout = QLabel()

        # Menyesuaikan ukuran gambar
        icon_size = QSize(150, 150)
        label_add_user.setPixmap(pixmap_add_user.scaled(icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        label_view_users.setPixmap(pixmap_view_users.scaled(icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        label_view_history.setPixmap(pixmap_view_history.scaled(icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        label_logout.setPixmap(pixmap_logout.scaled(icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Fungsi untuk menangani klik tombol
        def handle_click(action):
            clear_layout(self.layout)
            action()

        # Set label sebagai klik
        label_add_user.mousePressEvent = lambda event: handle_click(self.add_user)
        label_view_users.mousePressEvent = lambda event: handle_click(self.view_users)
        label_view_history.mousePressEvent = lambda event: handle_click(self.view_history)
        label_logout.mousePressEvent = lambda event: handle_click(self.logout)

        # Pusatkan gambar
        label_add_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_view_users.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_view_history.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_logout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Membuat label teks
        text_add_user = QLabel("")
        text_view_users = QLabel("")
        text_view_history = QLabel("")
        text_logout = QLabel("")

        # Pusatkan teks
        text_add_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_view_users.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_view_history.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_logout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tambahkan widget ke dalam grid layout
        grid_layout.addWidget(label_add_user, 0, 0)
        grid_layout.addWidget(text_add_user, 1, 0)
        grid_layout.addWidget(label_view_users, 0, 1)
        grid_layout.addWidget(text_view_users, 1, 1)
        grid_layout.addWidget(label_view_history, 2, 0)
        grid_layout.addWidget(text_view_history, 3, 0)
        grid_layout.addWidget(label_logout, 2, 1)
        grid_layout.addWidget(text_logout, 3, 1)

        # Tambahkan grid layout ke layout utama
        self.layout.addLayout(grid_layout)


    def add_user(self):
        dialog = AddUserDialog(self)
        dialog.exec()
        self.show_admin_mode()  # Kembali ke layout 4 tombol setelah dialog ditutup


    def capture_face(self, nim, folder):
        cap = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        print("Mulai scanning wajah...")
        count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                count += 1
                face_image = gray[y:y+h, x:x+w]
                face_image = cv2.resize(face_image, (100, 100))
                face_path = os.path.join(folder, f"face_{count}.jpg")
                cv2.imwrite(face_path, face_image)

                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            cv2.imshow('Face Detection', frame)

            if count >= 30:
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def view_history(self):
        self.clear_layout()

        # Membuka koneksi ke database
        conn = sqlite3.connect('face_detection.db')
        cursor = conn.cursor()

        try:
            # Mengambil data history dan biodata
            cursor.execute('''
                SELECT h.tanggal, h.nim, b.nama, b.alamat, b.hp, b.email 
                FROM history h
                JOIN biodata b ON h.nim = b.nim
                ORDER BY h.tanggal DESC
            ''')
            history_records = cursor.fetchall()  # Mengambil semua data histori
            print(f"Data histori yang diambil: {history_records}")  # Debugging

            if not history_records:
                print("Tidak ada data histori yang ditemukan.")  # Debugging

            # Menampilkan data histori dalam tabel
            self.history_table = QTableWidget()
            self.history_table.setRowCount(min(20, len(history_records)))  # Set jumlah baris
            self.history_table.setColumnCount(6)  # Enam kolom: Tanggal, NIM, Nama, Alamat, HP, Email
            self.history_table.setHorizontalHeaderLabels(["Tanggal", "NIM", "Nama", "Alamat", "HP", "Email"])

            # Set ukuran dan font tabel
            self.history_table.setFixedSize(575, 250)  # Atur ukuran tabel
            font = self.history_table.font()
            font.setPointSize(8)  # Atur ukuran font
            self.history_table.setFont(font)

            for i, record in enumerate(history_records[:20]):  # Hanya ambil 20 entri pertama
                self.history_table.setItem(i, 0, QTableWidgetItem(record[0]))  # Tanggal
                self.history_table.setItem(i, 1, QTableWidgetItem(record[1]))  # NIM
                self.history_table.setItem(i, 2, QTableWidgetItem(record[2]))  # Nama
                self.history_table.setItem(i, 3, QTableWidgetItem(record[3]))  # Alamat
                self.history_table.setItem(i, 4, QTableWidgetItem(record[4]))  # HP
                self.history_table.setItem(i, 5, QTableWidgetItem(record[5]))  # Email

            self.layout.addWidget(self.history_table)

            # Tombol Hapus Histori
            btn_delete_history = QPushButton("Hapus Histori")
            btn_delete_history.clicked.connect(self.delete_history)
            self.layout.addWidget(btn_delete_history)

            # Navigasi
            self.current_page = 0
            self.total_pages = (len(history_records) + 19) // 20  # Hitung total halaman

            # Tombol navigasi
            self.btn_back = QPushButton("Back")
            self.btn_next = QPushButton("Next")

            # Mengatur ukuran tombol
            self.btn_back.setFixedSize(80, 30)
            self.btn_next.setFixedSize(80, 30)

            self.btn_back.clicked.connect(self.show_previous_page)
            self.btn_next.clicked.connect(self.show_next_page)

            self.layout.addWidget(self.btn_back)
            self.layout.addWidget(self.btn_next)

            # Disable tombol jika tidak ada halaman sebelumnya atau berikutnya
            self.update_navigation_buttons()

            # Tombol kembali ke dashboard admin
            btn_admin_dashboard = QPushButton("Kembali ke Dashboard Admin")
            btn_admin_dashboard.clicked.connect(self.show_admin_mode)  # Mengarahkan ke dashboard admin
            self.layout.addWidget(btn_admin_dashboard)

        except sqlite3.Error as e:
            print(f"Kesalahan saat mengambil data histori: {e}")
        finally:
            # Menutup koneksi
            cursor.close()
            conn.close()

    def delete_history(self):
        reply = QMessageBox.question(self, 'Konfirmasi Hapus', 'Apakah Anda yakin ingin menghapus semua histori?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect('face_detection.db')
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM history")
                conn.commit()
                QMessageBox.information(self, "Berhasil", "Semua histori telah dihapus.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat menghapus histori: {str(e)}")
            finally:
                cursor.close()
                conn.close()
                self.view_history()  # Refresh the history view

    def show_previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_history_table()

    def show_next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_history_table()

    def update_history_table(self):
        # Membuka koneksi ke database
        conn = sqlite3.connect('face_detection.db')
        cursor = conn.cursor()

        try:
            # Mengambil histori untuk halaman saat ini
            offset = self.current_page * 20
            cursor.execute("SELECT * FROM history ORDER BY tanggal DESC LIMIT 20 OFFSET ?", (offset,))
            history_records = cursor.fetchall()

            for i, record in enumerate(history_records):
                self.history_table.setItem(i, 0, QTableWidgetItem(record[1]))  # Tanggal
                self.history_table.setItem(i, 1, QTableWidgetItem(record[2]))  # NIM
                self.history_table.setItem(i, 2, QTableWidgetItem(record[3]))  # Nama

            # Kosongkan baris yang tidak terpakai
            for j in range(len(history_records), 20):
                self.history_table.setItem(j, 0, QTableWidgetItem(""))  # Kosongkan baris yang tidak terpakai

            self.update_navigation_buttons()

        except sqlite3.Error as e:
            print(f"Kesalahan saat mengambil data histori: {e}")
        finally:
            # Menutup koneksi
            cursor.close()
            conn.close()

    def update_navigation_buttons(self):
        self.btn_back.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < self.total_pages - 1)

    def view_users(self):
        self.clear_layout()

        # Membuka koneksi ke database
        conn = sqlite3.connect('face_detection.db')
        cursor = conn.cursor()

        try:
            # Melakukan operasi SELECT untuk mengambil data pengguna
            cursor.execute("SELECT * FROM biodata ORDER BY nama ASC")  # Mengurutkan berdasarkan nama
            user_records = cursor.fetchall()  # Mengambil semua data pengguna

            # Menampilkan data pengguna dalam tabel
            self.user_table = QTableWidget()
            self.user_table.setRowCount(min(10, len(user_records)))  # Set jumlah baris
            self.user_table.setColumnCount(6)  # Enam kolom: NIM, Nama, Alamat, HP, Email, Aksi
            self.user_table.setHorizontalHeaderLabels(["NIM", "Nama", "Alamat", "HP", "Email", "Aksi"])

            # Set ukuran dan font tabel
            self.user_table.setFixedSize(575, 250)  # Atur ukuran tabel
            font = self.user_table.font()
            font.setPointSize(8)  # Atur ukuran font
            self.user_table.setFont(font)

            for i, record in enumerate(user_records[:10]):  # Hanya ambil 10 entri pertama
                self.user_table.setItem(i, 0, QTableWidgetItem(record[1]))  # NIM
                self.user_table.setItem(i, 1, QTableWidgetItem(record[2]))  # Nama
                self.user_table.setItem(i, 2, QTableWidgetItem(record[3]))  # Alamat
                self.user_table.setItem(i, 3, QTableWidgetItem(record[4]))  # HP
                self.user_table.setItem(i, 4, QTableWidgetItem(record[5]))  # Email

                # Tambahkan tombol hapus di kolom terakhir
                btn_delete_user = QPushButton("Hapus")
                btn_delete_user.clicked.connect(lambda checked, nim=record[1]: self.delete_user(nim))  # Pass NIM
                self.user_table.setCellWidget(i, 5, btn_delete_user)  # Menambahkan tombol ke tabel

            self.layout.addWidget(self.user_table)

            # Navigasi
            self.current_user_page = 0
            self.total_user_pages = (len(user_records) + 9) // 10  # Hitung total halaman

            # Tombol navigasi
            self.btn_user_back = QPushButton("Back")
            self.btn_user_next = QPushButton("Next")

            # Mengatur ukuran tombol
            self.btn_user_back.setFixedSize(80, 30)
            self.btn_user_next.setFixedSize(80, 30)

            self.btn_user_back.clicked.connect(self.show_previous_user_page)
            self.btn_user_next.clicked.connect(self.show_next_user_page)

            self.layout.addWidget(self.btn_user_back)
            self.layout.addWidget(self.btn_user_next)

            # Disable tombol jika tidak ada halaman sebelumnya atau berikutnya
            self.update_user_navigation_buttons()

            # Tombol kembali ke dashboard admin
            btn_admin_dashboard = QPushButton("Kembali ke Dashboard Admin")
            btn_admin_dashboard.clicked.connect(self.show_admin_mode)  # Mengarahkan ke dashboard admin
            self.layout.addWidget(btn_admin_dashboard)

        except sqlite3.Error as e:
            print(f"Kesalahan saat mengambil data pengguna: {e}")
        finally:
            # Menutup koneksi
            cursor.close()
            conn.close()

    def show_previous_user_page(self):
        if self.current_user_page > 0:
            self.current_user_page -= 1
            self.update_user_table()

    def show_next_user_page(self):
        if self.current_user_page < self.total_user_pages - 1:
            self.current_user_page += 1
            self.update_user_table()

    def update_user_table(self):
        # Membuka koneksi ke database
        conn = sqlite3.connect('face_detection.db')
        cursor = conn.cursor()

        try:
            # Mengambil data pengguna untuk halaman saat ini
            offset = self.current_user_page * 10
            cursor.execute("SELECT * FROM biodata ORDER BY nama ASC LIMIT 10 OFFSET ?", (offset,))
            user_records = cursor.fetchall()

            for i, record in enumerate(user_records):
                self.user_table.setItem(i, 0, QTableWidgetItem(record[1]))  # NIM
                self.user_table.setItem(i, 1, QTableWidgetItem(record[2]))  # Nama
                self.user_table.setItem(i, 2, QTableWidgetItem(record[3]))  # Alamat
                self.user_table.setItem(i, 3, QTableWidgetItem(record[4]))  # HP
                self.user_table.setItem(i, 4, QTableWidgetItem(record[5]))  # Email

            # Kosongkan baris yang tidak terpakai
            for j in range(len(user_records), 10):
                self.user_table.setItem(j, 0, QTableWidgetItem(""))  # Kosongkan baris yang tidak terpakai

            self.update_user_navigation_buttons()

        except sqlite3.Error as e:
            print(f"Kesalahan saat mengambil data pengguna: {e}")
        finally:
            # Menutup koneksi
            cursor.close()
            conn.close()

    def update_user_navigation_buttons(self):
        self.btn_user_back.setEnabled(self.current_user_page > 0)
        self.btn_user_next.setEnabled(self.current_user_page < self.total_user_pages - 1)

    def delete_user(self, nim):
        reply = QMessageBox.question(self, 'Konfirmasi Hapus', f'Apakah Anda yakin ingin menghapus user dengan NIM {nim}?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Hapus dari database
                cursor.execute("DELETE FROM biodata WHERE nim = ?", (nim,))
                cursor.execute("DELETE FROM history WHERE nim = ?", (nim,))  # Hapus juga dari history jika ada
                conn.commit()

                # Hapus folder image_data
                user_folder = os.path.join("image_data", nim)
                if os.path.exists(user_folder):
                    import shutil
                    shutil.rmtree(user_folder)  # Hapus folder beserta isinya

                QMessageBox.information(self, "Berhasil", f"User dengan NIM {nim} telah dihapus.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat menghapus user: {str(e)}")
            finally:
                self.view_users()  # Tampilkan kembali daftar pengguna setelah penghapusan

    def detect_face(self):
        cap = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        known_faces = []
        known_names = []

        cursor = sqlite3.connect('face_detection.db').cursor()
        cursor.execute("SELECT * FROM biodata")
        users = cursor.fetchall()

        for user in users:
            user_folder = os.path.join('image_data', user[1])
            faces_images = [f for f in os.listdir(user_folder) if f.endswith('.jpg')]
            for face_image in faces_images:
                img = cv2.imread(os.path.join(user_folder, face_image), cv2.IMREAD_GRAYSCALE)
                known_faces.append(img)
            known_names.append((user[1], user[0]))  # Store tuple (nama, NIM)

        is_absent = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                face = gray[y:y+h, x:x+w]
                face = cv2.resize(face, (100, 100))

                min_diff = float('inf')
                name = "Unknown"

                for i, known_face in enumerate(known_faces):
                    diff = cv2.norm(known_face, face, cv2.NORM_L2)
                    if diff < min_diff:
                        min_diff = diff
                        name = known_names[i]

                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

                if name != "Unknown" and not is_absent:
                    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    nim = next((nim for n, nim in known_names if n == name), None)
                    print(f"Menambahkan ke histori: Tanggal: {tanggal}, NIM: {nim}, Nama: {name}")  # Debugging
                    cursor.execute("INSERT INTO history (tanggal, nim, nama) VALUES (?, ?, ?)", (tanggal, nim, name))
                    cursor.connection.commit()  # Pastikan commit dipanggil
                    print(f"Data berhasil ditambahkan ke histori.")  # Debugging
                    is_absent = True
                    break

            cv2.imshow('Face Detection', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if is_absent:
                break

        cap.release()
        cv2.destroyAllWindows()

    def clear_layout(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

    def clear_user_data(self):
        # Hapus gambar dan biodata dari layout jika ada
        if self.camera_label:
            print("Menghapus camera_label...")
            self.layout.removeWidget(self.camera_label)
            self.camera_label.deleteLater()
            self.camera_label = None  # Set ke None setelah dihapus

        if self.user_data_label:
            print("Menghapus user_data_label...")
            self.layout.removeWidget(self.user_data_label)
            self.user_data_label.deleteLater()
            self.user_data_label = None  # Set ke None setelah dihapus

        self.layout.update()  # Memperbarui layout untuk menghilangkan ruang yang tidak terpakai

class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tambah User")

        layout = QFormLayout()

        self.nim_input = QLineEdit()
        self.nama_input = QLineEdit()
        self.alamat_input = QLineEdit()
        self.hp_input = QLineEdit()
        self.email_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_input = QLineEdit()  # New field for role

        layout.addRow("Masukkan NIM:", self.nim_input)
        layout.addRow("Masukkan Nama:", self.nama_input)
        layout.addRow("Masukkan Alamat:", self.alamat_input)
        layout.addRow("Masukkan Nomor HP:", self.hp_input)
        layout.addRow("Masukkan Email:", self.email_input)
        layout.addRow("Masukkan Username:", self.username_input)  # New field
        layout.addRow("Masukkan Password:", self.password_input)  # New field
        layout.addRow("Masukkan Role (user/admin):", self.role_input)  # New field

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit)
        self.back_button = QPushButton("Kembali")
        self.back_button.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.submit_button)
        buttons_layout.addWidget(self.back_button)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def submit(self):
        nim = self.nim_input.text()
        nama = self.nama_input.text()
        alamat = self.alamat_input.text()
        hp = self.hp_input.text()
        email = self.email_input.text()
        username = self.username_input.text()  # New field
        password = self.password_input.text()  # New field
        role = self.role_input.text()  # New field

        if nim and nama and alamat and hp and email and username and password and role:
            conn = sqlite3.connect('face_detection.db')
            cursor = conn.cursor()

            try:
                # Melakukan operasi INSERT
                cursor.execute("INSERT INTO biodata (nim, nama, alamat, hp, email, username, password, role) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (nim, nama, alamat, hp, email, username, password, role))
                conn.commit()  # Menyimpan perubahan
            except sqlite3.Error as e:
                print(f"Kesalahan saat melakukan operasi: {e}")
            finally:
                # Menutup koneksi
                cursor.close()
                conn.close()

            user_folder = os.path.join("image_data", nim)
            os.makedirs(user_folder, exist_ok=True)

            self.parent().capture_face(nim, user_folder)
            QMessageBox.information(self, "Berhasil", f"User {nama} telah ditambahkan dan wajah telah dipindai!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Semua kolom harus diisi!")

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    with open("error_log.txt", "a") as f:
        f.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    QMessageBox.critical(None, "Error", "Terjadi kesalahan. Silakan lihat error_log.txt untuk detail.")

sys.excepthook = handle_exception

def create_default_admin():
    conn = sqlite3.connect('face_detection.db')
    cursor = conn.cursor()

    # Cek apakah tabel biodata kosong
    cursor.execute("SELECT COUNT(*) FROM biodata")
    count = cursor.fetchone()[0]

    if count == 0:
        # Jika kosong, tambahkan admin default
        cursor.execute("INSERT INTO biodata (nim, nama, alamat, hp, email, username, password, role) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('admin_nim', 'Admin', 'Admin Address', '0000000000', 'admin@example.com', 'admin', 'admin', 'admin'))
        conn.commit()
        print("Admin default telah dibuat.")

    cursor.close()
    conn.close()

# Set light mode for the entire application
app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet("""
    QWidget {
        background-color: white;
        color: black;
    
    }
     QLineEdit {
        border: 2px solid black;
        background-color: white;
        color: black;
        border-radius: 10px;
        padding: 5px;
        font-size: 14px;
    }
    QLineEdit:focus {
        border: 2px solid gray;
        background-color: #f0f0f0;
    }           
    QPushButton {
        background-color: black;
        color: white;
        border: none;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: gray;
    }
"""
)

window = FaceDetectionApp()
window.show()
sys.exit(app.exec())

if __name__ == "__main__":
    create_default_admin()  # Buat admin default jika belum ada
    app = QApplication([])
    window = FaceDetectionApp()
    window.show()
    app.exec()
