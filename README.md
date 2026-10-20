# Green Lantern Ring – 3D viewer (bản Yosh Studios, đã chỉnh)

Trang xem 3D (three.js): xoay/zoom, tách rời bộ phận, cắt ngang, sửa kích thước (khung, độ dày khung, độ dày đá,
chu vi ngón) và tải STL đã chỉnh để in resin.

Mô hình gốc: **Yosh Studios** (Patreon, bản trả phí). Đã chỉnh:
- khung vàng thành **1 khối liền**: đáy đặc ~1.06 mm + thành ~1.06 mm có 5 lỗ cho đá (tổng ~2.13 mm)
- đá + đĩa dày **1 mm**, đặt trên mặt đáy khung

## Cấu trúc

```
public/index.html       viewer, đã nhúng sẵn mô hình  (thư mục deploy)
public/downloads/*.stl  file in đã chỉnh
models/source/          STL gốc của Yosh (ring_frame, gems, ring)
tools/build.py          sinh lại public/ từ models/source
tools/template.html     giao diện viewer
render.yaml             cấu hình Render (static site, publish: public)
```

## Chạy local

```bash
python -m http.server 8000 --directory public
```
Mở http://localhost:8000

## Sinh lại mô hình

```bash
pip install -r requirements.txt
python tools/build.py
```
Độ dày lỗ hở/đá chỉnh ở đầu `tools/build.py` (`CLEAR`, `GEM_T`).

## Lưu ý giấy phép

STL của Yosh là sản phẩm trả phí. Để dùng cá nhân thì không sao; **đừng đẩy `models/source/`, `public/downloads/` hay
`public/index.html` (có nhúng mô hình) lên repo/site công khai** nếu giấy phép Patreon của Yosh không cho phép phân phối lại.
