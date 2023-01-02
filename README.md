# Çok Disiplinli Tasarım Projesi Grup 80

## Dosya Hiyerarşisi

* controlling_robot/ :Robot arabaya bağlı Raspberry Pi'a yüklenip orada çalıştırılacak kodları barındırır.
* eye_tracking/ :Kamera bulunduran, göz takip işleminin yapılacağı bilgisayarda çalıştırılacak kodları barındırır.
    * app/
        *  eye_tracking.py : Görüntü işleme ve tespit edilen komutu MQTT protokolü ile uzak bilgisayara gönderme
            işlemleri için Thread'ler barındırır.
    * interface.py :PyQt5 ile yazılmış GUI'yi çalıştırır. GUI'den haberleşme ve göz takip işlemleri kontrol edilebilir.

## Çalıştırma Yönergesi

### Eye Tracking

* Gerekli Python paketleri yüklenir.
    ```sh
    pip install -r requirements.txt
    ```

* GUI çalıştırılır.
    ```sh
    python interface.py
    ```
