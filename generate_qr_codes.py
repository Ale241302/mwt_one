import os
import qrcode
import qrcode.image.svg

routes = {
    'gol': 'Goliath',
    'vel': 'Velox',
    'orb': 'Orbis',
    'leo': 'Leopard',
    'bis': 'Bison'
}

BASE_URL = "https://go.ranawalk.com/"
OUTPUT_DIR = "qr_codes"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for slug, product in routes.items():
    url = f"{BASE_URL}{slug}"
    # Generate PNG
    qr_png = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr_png.add_data(url)
    qr_png.make(fit=True)
    img_png = qr_png.make_image(fill_color="black", back_color="white")
    img_png.save(os.path.join(OUTPUT_DIR, f"{product.lower()}_qr.png"))
    
    # Generate SVG
    factory = qrcode.image.svg.SvgPathImage
    qr_svg = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
        image_factory=factory
    )
    qr_svg.add_data(url)
    qr_svg.make(fit=True)
    img_svg = qr_svg.make_image()
    img_svg.save(os.path.join(OUTPUT_DIR, f"{product.lower()}_qr.svg"))

print("Successfully generated SVG and PNG QR codes in the 'qr_codes' directory.")
