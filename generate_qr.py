import qrcode
import os

def generate_github_qr(github_url, output_path):
    # QR 코드 설정
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(github_url)
    qr.make(fit=True)

    # 이미지 생성 (RGB 모드로 생성하여 호환성 높임)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 저장
    img.save(output_path)
    print(f"QR Code successfully saved to: {output_path}")

if __name__ == '__main__':
    # 본인의 GitHub 주소로 변경하세요!
    your_github_url = "https://github.com/nli830052-cmd/YoulSystem.git" 
    output_file = "github_qr.png"
    
    generate_github_qr(your_github_url, output_file)
