"""
╔══════════════════════════════════════════════════════════════════╗
║               🤖 NPU Simulator                                   ║
║  ➡️ 실행: python main.py                                          ║
╚══════════════════════════════════════════════════════════════════╝

- 📋 목차
    - utils
        - 🟦 generate_cross(), generate_x(), generate_all_ones()
        - 🟦 generate_data_json()
        - 🟦 is_valid_grid()
        - 🟦 _print_grid()

    - core
        - 🟩 input_grid()
        - 🟩 normalize_label()
        - 🟩 mac()                    = 각각 Multiply-Accumulate 연산
        - 🟩 measure()                = 소요 시간 측정
        - 🟩 judge()                  = 유사도 결과 도출
        - 🟩 performance_analysis()   =

    - flatten
        - 🟪 flatten(), mac_1d(), measure_1d()

- 🔥 Mode1
    - input_grid()
    - mac()
    - measure()
    - judge()
    - performance_analysis()

- 🔥 Mode2
    - (read json file)
    - (road filter in json file)
    - nomalize_label()
    - mac()
    - measure()
    - judge()
    - performance_analysis()

- 🔥 main()

"""

import json 
import time 
import os   


def generate_cross(n): 
    mid = n // 2                           
    grid = [[0.0] * n for _ in range(n)]   
    

    for i in range(n):         
        grid[mid][i] = 1.0     
        grid[i][mid] = 1.0     

    return grid                


def generate_x(n): 
    grid = [[0.0] * n for _ in range(n)]   

    for i in range(n):                     
        grid[i][i] = 1.0                   
        grid[i][n - 1 - i] = 1.0           

    return grid                            


def generate_all_ones(n): 
    return [[1.0] * n for _ in range(n)] 


def generate_data_json(filepath="data.json"): 
    data = { 
        "filters": { 
            "size_5": {"cross": generate_cross(5), "x": generate_x(5)}, 
            "size_13": {"cross": generate_cross(13), "x": generate_x(13)}, 
            "size_25": {"cross": generate_cross(25), "x": generate_x(25)}, 
        }, 
        "patterns": { 
            "size_5_1": {"input": generate_x(5), "expected": "x"}, 
            "size_5_2": {"input": generate_cross(5), "expected": "+"}, 
            "size_5_3": {"input": generate_cross(5), "expected": "+"}, 
            "size_5_4": {"input": generate_cross(5), "expected": "x"}, 
            "size_13_1": {"input": generate_cross(13), "expected": "+"}, 
            "size_13_2": {"input": generate_x(13), "expected": "x"}, 
            "size_13_3": {"input": generate_all_ones(13), "expected": "+"}, 
            "size_25_1": {"input": generate_cross(25), "expected": "+"}, 
            "size_25_2": {"input": generate_x(25), "expected": "x"}, 
            "size_25_3": {"input": generate_cross(25), "expected": "+"}, 
        }, 
    } 

    with open(filepath, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4, ensure_ascii=False) 

    print(f"  ✓ {filepath} 자동 생성 완료 (10케이스)") 


def is_valid_grid(grid, n):  
    if not isinstance(grid, list):  
        return False  
    if len(grid) != n:  
        return False  
    for row in grid:  
        if not isinstance(row, list):  
            return False  
        if len(row) != n:  
            return False  
    return True  


def _print_grid(grid):  
    for row in grid:  
        nums = " ".join(str(int(v)) if v == int(v) else str(v) for v in row)  
        print(f"    {nums}")  



def input_grid(name, n): 
    """
    콘솔에서 n×n 숫자 배열을 입력받습니다.

    입력 방법:
        한 줄에 n개 숫자를 공백으로 구분 → n번 반복
        예(3×3): "0 1 0" → "1 1 1" → "0 1 0"

    검증:
        - 숫자 아닌 문자 → 오류 + 재입력
        - 개수 != n       → 오류 + 재입력

    반환값:
        list[list[float]]: n×n 2차원 배열
    """
    print(f"\n  {name} ({n}×{n}, 각 줄에 숫자 {n}개 / 공백 구분)") 

    grid = [] 
    while len(grid) < n: 
        row_idx = len(grid) 
        raw = input(f"    {row_idx + 1}번째 줄 ▶ ").strip() 

        try: 
            nums = list(map(float, raw.split())) 
        except ValueError: 
            print("    ⚠️ 입력 형식 오류: 숫자만 입력해 주세요. (예: 0 1 0)") 
            continue 

        if len(nums) != n: 
            print(f"    ⚠️ 입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.") 
            print(f"      (입력 개수: {len(nums)}개, 필요: {n}개)") 
            continue 

        grid.append(nums) 

    return grid 


def normalize_label(raw): 
    key = raw.strip().lower()   # 공백 제거 + 소문자로 통일
                                # 예: '  Cross  ' → 'cross'
    if key in ("+", "cross"):   # + 또는 cross라면
        return "Cross"          # 표준 라벨 Cross 반환
    if key == "x":              # x라면
        return "X"              # 표준 라벨 X 반환
    return None                 # 알 수 없는 라벨


def mac(pattern, filter_2d):  
    """
    MAC(Multiply-Accumulate) 연산.

    같은 위치 값끼리 곱하고 모두 더해서 유사도 점수 반환.
    점수가 높을수록 패턴이 필터와 더 유사합니다.

    매개변수:
        pattern   (list[list[float]]): 입력 패턴 (2차원 배열)
        filter_2d (list[list[float]]): 비교 필터 (2차원 배열)

    반환값:
        float: 유사도 점수
    """
    score = 0.0  

    for i in range(len(pattern)):  
        for j in range(len(pattern[i])):  
            score += pattern[i][j] * filter_2d[i][j]  
            

    return score  


def measure(pattern, filter_2d, repeat=10): 
    """
    MAC 연산을 repeat번 반복 측정 후 평균 시간(ms) 반환.
        반환값:  float: 평균 연산 시간 (밀리초)
    """
    total = 0.0 

    for _ in range(repeat):        
        t0 = time.perf_counter()   
        mac(pattern, filter_2d)    
        t1 = time.perf_counter()   
        total += t1 - t0           

    return (total / repeat) * 1000 


def judge(score_a, score_b, label_a="Cross", label_b="X", epsilon=1e-9):  # 두 점수 중 더 큰 라벨을 고르는 함수
    if abs(score_a - score_b) < epsilon:   
        if label_a == "Cross":             
            return "UNDECIDED"              
        return "판정 불가"                   

    if score_a > score_b:                  
        return label_a                     
    return label_b                         


def performance_analysis(sizes, loaded_filters=None):
    print("\n" + "#" * 50)                          
    print("# [3] 성능 분석 (평균/10회 반복)")       
    print("#" * 50)                                 
    print(f"\n  {'크기':<12} {'평균 시간(ms)':<20} {'연산 횟수(N²)'}")  
    print("  " + "-" * 46)                          

    for n in sizes:                                 
        if loaded_filters and n in loaded_filters:  
            cross_f = loaded_filters[n]["Cross"]    
        else:                                       
            cross_f = generate_cross(n)             
        pattern = generate_cross(n)                 
        
        avg_ms = measure(pattern, cross_f)              

        print(f"  {n}×{n:<9} {avg_ms:<20.4f} {n*n}")    

    print("\n\n\n  [시간 비교] 2DArr vs 1DArr 성능 비교")                   
    print(f"\n  {'크기':<10} {'2D(ms)':<18} {'1D(ms)':<18} {'변화'}")     
    print("  " + "-" * 52)  

    for n in sizes:                                 
        if loaded_filters and n in loaded_filters:  
            cross_f = loaded_filters[n]["Cross"]    
        else:                                       
            cross_f = generate_cross(n)             
        pattern = generate_cross(n)                 

        t2d = measure(pattern, cross_f)             
        t1d = measure_1d(pattern, cross_f)          

        if t2d > 0:                                 
            pct = (t2d - t1d) / t2d * 100           
            sign = "↑빠름" if pct > 1 else ("↓느림" if pct < -1 else "→유사")  
        else:  
            pct, sign = 0.0, "→유사"                 

        
        print(f"  {n}×{n:<7} {t2d:<18.4f} {t1d:<18.4f} {sign}({abs(pct):.1f}%)")  

    print("\n  * Python에서 1D 효과는 미미하지만, 실제 NPU 하드웨어에서는 유의미.")  


def flatten(grid): 
    """
    2차원 배열을 1차원 배열로 납작하게 펴기.
    변환 공식: 1D 인덱스 k = 행(i) × N + 열(j)
            예: [[0,1,0],[1,1,1],[0,1,0]] → [0,1,0,1,1,1,0,1,0]
    반환값:
        list[float]: 1차원 배열
    """
    result = []                
    for row in grid:           
        for val in row:        
            result.append(val) 
    return result              


def mac_1d(flat_pattern, flat_filter):             
    """
    1차원 배열끼리 MAC 연산 (단일 반복문).
    결과 점수는 mac()과 완전히 동일.
    반환값: float: 유사도 점수
    """
    score = 0.0 
    for k in range(len(flat_pattern)):             
        score += flat_pattern[k] * flat_filter[k]  
    return score 


def measure_1d(pattern, filter_2d, repeat=10):     
    """
    1D MAC 연산 시간 측정.
    flatten은 I/O 준비 단계로 미리 처리, 측정에서 제외.

    반환값:
        float: 평균 연산 시간 (밀리초)
    """
    flat_p = flatten(pattern)                  
    flat_f = flatten(filter_2d)                

    total = 0.0                                
    for _ in range(repeat):                    
        t0 = time.perf_counter()               
        mac_1d(flat_p, flat_f)                 
        t1 = time.perf_counter()               
        total += t1 - t0                       

    return (total / repeat) * 1000             




def mode1():
    N = 3  # 3x3을 원하니 hardcoding

    print("\n" + "#" * 50)              
    print("# [1] 필터 입력 (입력층)")       
    print("#" * 50)                     

    filter_a = input_grid("필터 A", N)  
    filter_b = input_grid("필터 B", N)  

    print("\n  ✓ 필터 A:")               
    _print_grid(filter_a)               
    print("\n  ✓ 필터 B:")               
    _print_grid(filter_b)               

    print("\n" + "#" * 50)              
    print("# [2] 패턴 입력 (입력층)")   
    print("#" * 50)                     

    pattern = input_grid("패턴", N)     
    print("\n  ✓ 패턴:")                
    _print_grid(pattern)               

    score_a = mac(pattern, filter_a)   
    score_b = mac(pattern, filter_b)   

    avg_ms = measure(pattern, filter_a, repeat=10) 

    verdict = judge(score_a, score_b, label_a="A", label_b="B")

    print("\n" + "#" * 50)                          
    print("# [3] MAC 결과 (은닉층 → 출력층)")       
    print("#" * 50)                                 
    print(f"\n  A 점수: {score_a:.16f}")            
    print(f"  B 점수: {score_b:.16f}")              
    print(f"  연산 시간(평균/10회): {avg_ms:.3f} ms")

    if verdict == "판정 불가": 
        print("  판정: 판정 불가 (|A-B| < 1e-9)")    
    else:  
        print(f"  판정: {verdict}")               

    performance_analysis(sizes=[N])               



def add_fail(fails, case_id, reason):             
    print(f"  ⚠ {reason} → FAIL")                
    fails.append((case_id, reason))               
    return 1                                      

def mode2():
    json_path = "data.json"

    if not os.path.exists(json_path):                 
        print(f"\n  ⚠ {json_path} 없음 → 자동 생성...")  
        generate_data_json(json_path)                 

    with open(json_path, "r", encoding="utf-8") as f: 
        data = json.load(f)                           

    print("\n" + "#" * 50)           
    print("# [1] 필터 로드")         
    print("#" * 50 + "\n")           

    loaded_filters = {}          

    for size_key, filter_dict in data.get("filters", {}).items():
        try:                                                     
            n = int(size_key.split("_")[1])                      
        except (IndexError, ValueError):                         
            print(f"  ⚠ 필터 키 파싱 실패: '{size_key}' (건너뜀)")     
            continue                                             

        cross_f, x_f = None, None                                

        for fkey, fval in filter_dict.items():                   
            lbl = normalize_label(fkey)                          
            if lbl == "Cross":                                   
                cross_f = fval                                   
            elif lbl == "X":                                     
                x_f = fval                                       

        if cross_f is None or x_f is None:                           
            print(f"  ⚠ {size_key:<10} 불완전 (Cross 또는 X 없음)")      
            continue                                                 
        if not is_valid_grid(cross_f, n) or not is_valid_grid(x_f, n):  
            print(f"  ⚠ {size_key:<10} 크기 오류 (필터가 {n}×{n} 형식이 아님)")
            continue                                                    

        loaded_filters[n] = {"Cross": cross_f, "X": x_f}                
        print(f"  ✓ {size_key:<10} 로드 완료 (Cross, X)")                 

    print("\n" + "#" * 50)                  
    print("# [2] 패턴 분석 (라벨 정규화 적용)")   
    print("#" * 50)                         

    total, passed, failed = 0, 0, 0            
    fails = []                                 

    for case_id, case_data in data.get("patterns", {}).items(): 
        print(f"\n  --- {case_id} ---")                         
        total += 1                                              
    
        try:                                                   
            n = int(case_id.split("_")[1])                     
        
        except (IndexError, ValueError):                       
            reason = "케이스 키 파싱 실패"                          
            failed += add_fail(fails, case_id, reason)         
            continue                                           
    
        if n not in loaded_filters:                            
            reason = f"size_{n} 필터 없음"                       
            failed += add_fail(fails, case_id, reason)         
            continue                                           
    
        cross_f = loaded_filters[n]["Cross"]               
        x_f = loaded_filters[n]["X"]                       

        pattern_input = case_data.get("input")             
        if pattern_input is None:                          
            reason = "input 필드 없음"                       
            failed += add_fail(fails, case_id, reason)     
            continue                                       
    
        if not is_valid_grid(pattern_input, n):            
            reason = f"크기 불일치 (패턴이 {n}×{n} 형식이 아님)"  
            failed += add_fail(fails, case_id, reason)     
            continue                                       
    
        expected = normalize_label(case_data.get("expected", ""))          
        if expected is None:                                               
            reason = f"알 수 없는 expected: '{case_data.get('expected')}'"   
            failed += add_fail(fails, case_id, reason)                     
            continue                                                       
    
        score_cross = mac(pattern_input, cross_f)          
        score_x = mac(pattern_input, x_f)                  

        result = judge(score_cross, score_x, label_a="Cross", label_b="X") 
    
        if result == "UNDECIDED":                          
            outcome = "FAIL"                               
            reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"    
        elif result == expected:                           
            outcome = "PASS"                               
            reason = ""                                    
        else:                                              
            outcome = "FAIL"                               
            reason = f"판정={result} ≠ expected={expected}" 

        print(f"  Cross 점수: {score_cross:.16f}") 
        print(f"  X 점수    : {score_x:.16f}") 
        print(f"  판정: {result:<10} | expected: {expected:<6} | {outcome}") 

        if outcome == "PASS": 
            passed += 1 
        else: 
            failed += 1 
            fails.append((case_id, reason)) 

    performance_analysis(sizes=[3, 5, 13, 25], loaded_filters=loaded_filters)

    print("\n" + "#" * 50)                   
    print("# [4] 결과 요약")                     
    print("#" * 50)                              
    print(f"\n  총 테스트: {total}개")          
    print(f"  통과    : {passed}개")            
    print(f"  실패    : {failed}개")            

    if fails:                               
        print("\n  실패 케이스:")               
        for cid, rsn in fails:              
            print(f"    - {cid}: {rsn}")    
    else:                                      
        print("\n  ✓ 실패 케이스 없음!")           


def main(): 
    print("\n" + "=" * 50) 
    print("    🤖  NPU Simulator  🤖") 
    print("=" * 50) 
    print() 
    print("[모드 선택]") 
    print("  1. 사용자 입력 (3×3) — 직접 숫자 타이핑") 
    print("  2. data.json 분석    — 파일 자동 로드 및 채점") 

    while True: 
        choice = input("\n선택 (1 또는 2) ▶ ").strip() 
        if choice == "1": 
            mode1() 
            break 
        elif choice == "2": 
            mode2() 
            break 
        else: 
            print("  ⚠ 1 또는 2를 입력해 주세요.") 

    print("\n" + "=" * 50) 
    print("  ✅  NPU Simulator 종료") 
    print("=" * 50 + "\n") 


if __name__ == "__main__": 
    main() 
