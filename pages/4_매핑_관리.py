import streamlit as st
import mapping
import importlib

def main():
    st.title("⚙️ 데이터 매핑 관리")
    st.subheader("나라 코드 및 항구 매핑 추가")

    # 1. 현재 매핑 데이터 불러오기
    current_map = mapping.COUNTRY_PORT_MAP

    # 2. 데이터 추가 입력 UI
    with st.form("add_mapping_form"):
        new_code = st.text_input("국가 코드 (예: KR, US)", placeholder="DR").upper().strip()
        new_ports = st.text_area("항구 및 국가명 (줄바꿈으로 여러 개 입력)", 
                                placeholder="CAUCEDO, DOMINICAN REP.\nRIO HAINA, DOMINICAN REP.")
        
        submit_btn = st.form_submit_button("매핑 데이터 추가 및 저장")

    if submit_btn:
        if new_code and new_ports:
            # 줄바꿈으로 입력된 항구들을 리스트로 변환
            port_list = [p.strip() for p in new_ports.split('\n') if p.strip()]
            
            # 기존 데이터에 병합 (이미 있으면 업데이트)
            current_map[new_code] = port_list
            
            # 3. mapping.py 파일 업데이트 (파일 쓰기)
            try:
                with open("mapping.py", "r", encoding="utf-8") as f:
                    lines = f.readlines()

                with open("mapping.py", "w", encoding="utf-8") as f:
                    # COUNTRY_PORT_MAP 정의 시작 부분 찾기
                    found_start = False
                    for line in lines:
                        if "COUNTRY_PORT_MAP = {" in line:
                            f.write(f"COUNTRY_PORT_MAP = {current_map}\n")
                            found_start = True
                        # 기존 딕셔너리 안의 내용들은 건너뜀 (이미 합쳤으므로)
                        elif found_start and line.strip().startswith("}"):
                            found_start = False
                            continue
                        elif found_start:
                            continue
                        else:
                            f.write(line)
                
                st.success(f"✅ {new_code} 매핑이 저장되었습니다!")
                importlib.reload(mapping) # 변경된 내용 즉시 적용
            except Exception as e:
                st.error(f"🔴 파일 저장 중 오류 발생: {e}")
        else:
            st.warning("코드와 항구 내용을 모두 입력해주세요.")

    # 4. 현재 매핑 현황 확인
    st.divider()
    st.write("📊 현재 등록된 매핑 리스트")
    st.json(current_map)

if __name__ == "__main__":
    main()
