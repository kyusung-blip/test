def handle_etc(data, e_type="입고방"):
    """
    data: buyprogram.py에서 수집한 입력값 딕셔너리
    e_type: 버튼 종류 ('입고방', '서류문자')
    """
    if e_type == "서류문자":
        return """말소

**개인사업자 경우
자동차등록증 원본
사업자등록증
자동차관리사업등록증(상품용인 경우)
대표자 신분증 사본

**법인사업자 경우
자동차등록증 원본
사업자등록증
자동차관리사업등록증(상품용인 경우)
법인인감증명서 원본(3개월이내)
법인등기부등본 사본

서류는 출고시 차량에 넣어주세요.

010-****-1019
말소증은 이쪽번호에서 발송되며,
통상적으로 탁송 다음날 말소가 진행되니
하루정도 감안해주시면 감사하겠습니다.

"탁송 다음날 저녁"까지 말소증을 못받았을 시,
차량번호와 차종을 알려주세요."""

    # --- 입고방 로직 ---
    buyer = data.get('buyer', '').upper()
    region = data.get('region', '')
    vin = data.get('vin', '')
    km = data.get('km', '')
    h_type = data.get('h_type', '선택')
    h_id = data.get('h_id', '선택')
    auc_type = data.get('auc_type', '선택')
    auc_region = data.get('auc_region', '') # 옥션 전용 지역
    
    car_name = data.get('car_name_remit', '')
    plate = data.get('plate', '')
    year = data.get('year', '')

    # ID 관련 푸터 구성
    h_id_display = h_id if h_id != "선택" else "ID 미선택"
    export_tag = " , 수출전용 아이디)" if h_id == "leeks21" else ")"
    footer_line = f"(사전판매완료 id: {h_id_display}{export_tag}"
    buyer_line = f"(사전판매 {buyer})"

    # 1. 헤이딜러 입고
    if h_type != "선택":
        message = f"{buyer_line}\n\n"
        message += f"헤이딜러 {h_type} 입고예정 (사전판매완료 id: {h_id_display} )\n"
        message += f"차번호: {plate} // {year} {car_name}\n"
        message += f"VIN: {vin}\n\n"
        message += footer_line
        return message

    # 2. 옥션 입고
    if auc_type != "선택":
        # 옥션 타입별 문구 생성
        auc_names = {
            "현대글로비스": "오토벨",
            "오토허브": "오토허브",
            "롯데": "롯데",
            "K car": "K car"
        }
        auc_display = auc_names.get(auc_type, auc_type)
        return f"{buyer} {auc_display}{auc_region} {vin} {km}"

    # 3. 일반 입고 (기본값)
    return f"{buyer} {region} {vin} {km}"
