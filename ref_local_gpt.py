import json
import os
import numpy as np
import time
import base64

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
#from oai_online.utils._construct_data import construct_data_for_model
#from oai_online.utils._extract_response import get_response_from_model

vision_models = ['step-1o-vision-32k', 'moonshot-v1-8k-vision-preview']#, 'o1-2024-12-17']
doubao_model_name_to_ep = {
     'doubao-pro-32k-240828': "ep-20241206174646-cxc4w",
     "doubao-pro-32k-241215": "ep-20241227205519-5f4w4",
     "doubao-pro-256k-241115": "ep-20250107145704-ghh97",
     "doubao-1-5-thinking-pro-250415": "doubao-1-5-thinking-pro-250415",
    }

def get_gpt_response(messages, model_version, temperature=0, max_tokens=4096, max_try=5, response_format = '', reasoning_effort = 'medium', debug=False):
    """Get response from GPT model using minimax API
    Args:
        messages (list): list of dict with keys 'role' and 'content', e.g.: [{'role': 'system', 'content': 'You are a
        helpful assistant.'}, {'role': 'user', 'content': '1+1和1*1哪个大'}]
        model_version (str): model version to use: 'gpt-4-1106-preview', 'gpt-4-32k-0613', 'gpt-4-turbo-2024-04-09',
        'gpt-4o-2024-05-13', 'gpt-4o-2024-08-06' etc.
        temperature (float): sampling temperature: less than 2.0
        max_tokens (int): maximum number of tokens to generate: less than 4096
        max_try (int): maximum number of tries to call the API
    Returns:
        str: response text
    """

    # Check input
    for message in messages:
        assert 'role' in message and 'content' in message
        assert message['role'] in ['system', 'user', 'assistant']

    assert 0.0 <= temperature <= 2.0
    if model_version in ['gpt-4-1106-preview', 'gpt-4-turbo-2024-04-09', 'gpt-4o-2024-05-13']:
        assert 0 < max_tokens <= 4096
    elif model_version == 'gpt-4-0613':
        max_tokens = min(max_tokens, 1024)

    max_try = int(os.environ.get('MINIMAX_GPT_MAX_TRY', max_try))

    model_version_proxy = 'gpt-4-0613' if model_version == 'gpt-4-32k-0613' else model_version

    # Get token
    model_map_token = {
        'gpt-4-1106-preview':
        ('10QZa0zVBn2eJdlFj75IJmVZO_Mp5qM1CQlhFM9HAXo6oeP5pF3RamEbqjwo-suLLmX4Oq5YVs-K-hGNiQattYZ9TN-BPkZgy0RUTqleoU0Sb2_gK5xu9LnXmtIUbPuban2arm7Le7yzehTMWUfbDQ==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhilian, qps10
        #('lp3HvMB9sgAVlZN11QREvZ6-9jdx9A39qjX7VcRMvxgFtcjpZvVgf357ezMO0OhQmS4SNLSGKVg0-sfd7zdssa002pwPmIZh_GZGE-cBDOF0nnfXiqiC4iB4UIwAns5zJICDfnz2ZE3vE89ukMkU3Q==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhongzhuan, qps10
        
        'gpt-4-0613': 
        ('9GPKS5C2ugGKgy_rNLl5QHY3i9XoJVk4BGR1Jbs_5fR4zN5lOgBMFC1-LGYkI1C2WC5tM_zFeFKi7ea0sgahz8qARM0a0ek1SicPAsUypLNl0y3Ks2CyMfmZC9iHCUc8', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhilian, qps10
        #('BI1ivDlsovTm3PZn7ibkoGAtIp5n-xCN0IcmXb52j8cG2Rwf5Ruj_PFI7IQXUsgxpL-FcF8EiFHn8PZnrA7IsloooOd1jKUC2hXCIr68kC4s5mFypK3QZKqIsqEicGtT', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhongzhuan, qps10
        
        'gpt-4-turbo-2024-04-09': 
        #('VNrGNTpuSJ4FUYDmX1DOTuPD4q378JP66k6VuiYuQR3iMqjVbUKjR8YcSRFttKrr7VsPIlAbqqLmf64hDU1Fm-aydsq80Oeiz0BQnnbFQioPFCreQr4HmXGYElTZNUkpzWUbTWco8oYk5NX8ANe5iw==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhilian, qps10
        ('dGmE7rZbt63qV66omdfe06AcnUFvNWx_5aXzs1HRrvDkFcFpLNotEJ1h-7JQZHwkE7vX7NWWXTCVlkX1I95po8L3giEdgyrtHdtq5URdveEjbw_durejf-wk8OdNGvBLfVYxz7kntQ_6F2Ax8W6Ikw==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhongzhuan, qps10
        'gpt-4o-2024-05-13':  
        #('vDhqGncyphBy-WuTvEYn5yM_-8coc_qgJuvJaJP7iw-3vzlLGfN2bG9-BtdmE8cdD8T7WmxdruIBdxmdxCoCiRp6uJT_vQCYHw9AcMOJG4ywGTiXqosiws99jXqdS82fAQGrEMlpkBy6zmYVSowx0g==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhilian, qps20
        ('LlHgGeuD4YrEllt34zEPjBl9mSgSL4hpHojk8ZD1FS3HwK6mZNxEZkGJs7Kkei3GdjuLDt1tPbF0aolrsws0jEdYrdD-TQ3zGXhCo1Pzc3SWK7rV6EmtiDVViPpI_SBBCsovkRcfII4GHMEOQpq4bw==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhongzhuan

        'gpt-4o-2024-08-06': 
        #('q8qQbEp6LJ58VKnx36mxtAsb2D5lpdGba_7E7GWcMlM_-ZyT-G3G3I1rcD_O4t3C-ohOUNo_sl0SWierbBTHaken7nCxatLq2E49LJvi5fg71_aI1uspwSrF4SooB79C6-HIuYi6kSMjyCk_6ldhvQ==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhilian, qps10
        ('R1_33TyuNMmC3MTmOe_jLCg7w9k9T4UVjOc-Iq3xIndNNQ28WFaTHylFOIX-qvEhyI5SznhR81Z8vTl4vh6GCgTbBoWPdSLv0aY8wuSFfkk0Zf7uo_glMGeJ0EVZtXmGb9DfHmtuRp1BF0UTALPhgg==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhongzhuan, qps10

        'claude-3-5-sonnet-20240620': ('Os1b_yrmgA51D1X-tZ8Ks9FF0hol-DopNsNxeW0MJBjgk_42OztFOXhkBh27lH_nX6Mh6r8_l9vTFQ5cadYQ12UULu5xbSXM_TZJ9DT3-P5HNNzSXOGHJCp8mimxzeaUNSZLyKIK6I4q_iJPMeHoNA==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # new, qps5

        'claude-3-5-sonnet-20241022':('BUT1RWeFjZ9g7H7O9tgvKdlmc_UJF9_Lqm9_EI-SRrvdzPEMWWmarXE9uZ3NImR-gKw5XkxcpqTaH-jIbE6kJ9tf5mXPJwnaD2yfR4_H7jTBItAiir0mxNtnx4B2bdOuZMKYIjShqqv5oL9cW6WXZA==','ac4a9e799a01963a8c3893a558b215b5fd7948b0890d7e12d490216cb54471dc'), # new

        'claude-3-7-sonnet-20250219':('yUBXh0DiogJ1DP13CrReIw_5NtU01C_gbjgzI3VGnsi7N5Ez_jhr3cPMISIq_sR0zls7W-wz7F4PcSGfcq_lEpaQ_RKYjC_ILuaut6sxxG5b9mYYSdXPVsohiUHw7XTbBB-kZbupeDnvoTdhtck7PA==','610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # new
        
        'claude-3-7-sonnet-20250219':('Lkk4I4FGKfKzeaxnObtmyOGqEZMcfkI3spA-M7eOQeLwkKQe5awmuj1s30vJezT0QJM7l-2uSzdZYqZ77sfHYkeeOnow5vXDa72WAgPmIH0pq33BrKGgN4S05xIeLS9-oEglfAFWG9Ag0Wa8vyFZ9A==','610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # new
        
        'o1-preview': 
        #('ijJMhfgR0fX68dDYi9TjJjY3h5fDo1J3rFqvjcmUy7SJg2iPHCHB9MLoQNE4tzWfL0-WqdkgbtESjFrI3LFXtQkDgFCOlRMJbIS2aNgoAO_1H0g4zpAHmjIa2QcOsZcJ', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # zhilian, qps1
        ('gYqF0z5MT6xB5HByEgW8wwW1XRx8-rUw1fZ1IztxLOmd2brvGUm9E1pPK5F64E1zjnDlvOotNF_jzxIQfq8K7dvn0g21NbQXt5e1gVYbU6qPCIdJbRbamXc8ct0r1ScmL3eNI3waaWz6PNkgqB2ntw==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # zhongzhuan, qps1

        'o1-mini': #('c6fEnzypiyq-lajE-atvHG6UrNH2kD82QO-87YPw7uhynNxiFIwaLxCGXUKyWua2rqAGW4-EcrfgszJRkfnlG-IYlVHDWB373ZSfuC8WndghvDLTuFBUhL1QIySBYz-C', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # zhilian, qps1
        ('sWKOGQjWeYQbJjky7Sdy5hxGe6diWqGwDmNbNRJqalStHLQxStSJVeLOugZUYJZn2KBm_b7IRURZeO7GehP19xuTszDLm6nDkczPJ1j8aigcEUxQk1tWmEnnNMghXj2Y', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # zhongzhuan, qps1

        'o3-mini':
        ('WDHShk-WnznoA01nMUT32EP3zBAeT_17uUANvgwkx_Z7RFC9TUrSggoH4nhjPmfkY1tKMlK3q2tAnINOA1Q5X76jU-caGIA-_-N7hznq40TxWKD8z6Dq4pGzf2RIXth8', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # zhongzhuan, qps1

        'o1-2024-12-17': ('edWpXbJATMHQ_HXYLqg99stpJ3lYHHi6TrJh1KWwVZzeIT8yRq5YgLvMoHo_egpsnsQK-FYStiTk4-TgwLvhoKcWDtkyPN4KcsF-DNpy1fab9iEA3KhmrZ1puikt9Xc4_QoVmI2a4jxfDEFd15zU0Q==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'), # new, qps5

        'chatgpt-4o-latest':
        ('Ai4p2ITp1bBbxozFec0Qg0z6o1HxP5Cl68X9htQVJwqQVHitMZp3D5vQBJbY2Qbgi1jR1pT8kkNxeDt5PUciQCF3R53daG4IJPJVZvUhudUrb0jdFGyIlqkKgQJvVIn2QaxQyU1RvvHLYUd_hgw2pA==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),
        
        'claude-sonnet-4-20250514':
        ('7ENu46Lrftpy1s-mjdEJQvzc94KTrDEzVCBh2otsJg-MvF_4gBLCOV3SKS77rfrnkFnmQkDOsx5ueztCwMynRK4gzmY1T1crPtrW-v6VE58geYfYPWvaFaolRMYZ8RY6V3GjJgXRhG7QuBch-9MM7Q==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'yi-lightning': ('I9sG19mIO5ePKf_I-XWGMl0bp77jURMa2dlcNiuW5GLil_ZIu5O_TcCJS_-rOe__93raTalpJeZfNo8afcFTwz3mN05jd3JIolhEO1VxFnQGPj2D0oRcJCUWDjWZi7nn','1ecd376900ed3fef82397be137e062dc61fcb7245c0eff01f478b71e0dcf9403'), # new

        'gpt-4o-2024-11-20':
        #('9pnyIS1hA8hin0z6JVD20Q3qjE3Epr5_gWAifKPWnRJfHuKb-pCaSCc5Gy_-UBY1jg8XXPx-NWj0a7zSJ8KdvdSXxIg82xpfzS2-UTxFT19VR-eHnaSCgO2Fe4byIB4MuZUgAjX7TcfK46TMnSNguw==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhilian, qps10
        ('Jctaakf7hHX9oml-pUYXcsYjUVgMceKZIP202DzBZ3FOCfl2nKNNu3v0V6M-wuKiQ-H5piAl1Ysti4Eql953Wn-dK3WGBHThqj8NkeBj_jV_7M4E9qhDAHkcavmJxMJmdXPiBRBeZYrEaatvHvsmOw==', '5e08875459232e487e6c55a177c6f7b0f68ecca4acc3dd1e827e2fb544fd1507'), # zhongzhuan, qps20

        'gemini-1.5-pro-latest': ('ZSy5kCDtXRaow4GxQG0RxIwc5fMK4Mt28GDTl9ecVqiP_Ukged2k4FPwh0YUw1P2tgMi0K0CDL7oSSHRkHi2G22oAfXO-mOl0E9zalx5_IfU2YZdrEwWdZ4RbAaHN_zJm-_AHjVZuH1M_yyCVLNEgg==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'gemini-2.0-flash-thinking-exp-01-21': ('b7NIEhXYoSu8G8GLKrLiZd4rVNmWD8SibKCEetjQETkyaEF842vE--OisyzxshmWWX_4Ht811XDdwKUpQtaPBKQoW37mUmWRsVv7-J28FjXDYut0aJqh0zeg-AJ2DrbUDs6kfs6k6Ti97MGXPl8jZ9-YqJN4hp6299cmomp--5Y=', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'gemini-2.0-flash-exp': ('7s0QP7eaqWeTOUAAJe7Xr6GMP_AKosR9Cp4XPwx2UeiAdFa5yRP5kUqrY9bZPMzcEOYqVbSj4Sloc8p_z7QQeIiNl40Al7bDFN5rpaGA4zuzlgObgUgTfkGv7vUJUPIP45x2ZV5YLFUxO7pdn99-3JquETDJm5RhMXs4zJ95vn8=', 'a67a809ff844afe0b9d9ebac46dbd4abbc01662d573ac49279d33dde2ec31bac'),

        'gemini-exp-1206': ('E8JhTBUvBBAeomWw2R_V9lfLyTl299B3doWFK5XstuspNKMDl7wT7VjQ92wO6iXU8CGSfnnxpu03JccK8Nawmw-GuexMR94T17-X4FWsjkAg4isXLaU6uCmgWaOIe1PrB4xVPGd7ZoUbKygG1FEnrA==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'gemini-2.0-pro-exp-02-05':
        ('osDgQWgCMBA1bmilVvP6uqfHTtXcpUT4aW7DXHRZGu0UP55cGPH2s7E8pyLds0epMaBYhknay183z9D-jY-L1c7mFXpMRs_G8-HTkn_GdYlWseAcjw0Fl6eFd0oN9jfTzoKB124dO-z6FxqbpN9nLQ==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'gemini-2.5-pro-preview-03-25': ('PsNkRoJdizPhEdICzFKiruN4iPw_Foi8Vg2T3_WliikHxgdDwtu71gY6s5rrhfLn6XTBCox9ZkLTRZF2ZomKw5vpauD5qKQpLcl03gF3ak5fIG8N3eMN2s6ATxz0OhkdyjK0Eqapwk-uzSGKe-dVS62iN1pv1aKKz3B2cfSNiq4=', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'qwen-max-2024-09-19':
        ('BVTI59azmpbz_QfdY3F3Vj56Uw1k49UnAdIHieSZVQSkQNfoP1xtLtU6bHzol3QyK3MnpBTZvpROXM5cDUxe9MB7wMnOwqmf0WkciuTsAunLobX0L--Y_m-4uL5zr1EOEYXqwAKKuXma7_ienhJ1-g==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'qwen-long':
        ('BVTI59azmpbz_QfdY3F3Vj56Uw1k49UnAdIHieSZVQSkQNfoP1xtLtU6bHzol3QyK3MnpBTZvpROXM5cDUxe9MB7wMnOwqmf0WkciuTsAunLobX0L--Y_m-4uL5zr1EOEYXqwAKKuXma7_ienhJ1-g==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'qwen-math-plus':
        ('BVTI59azmpbz_QfdY3F3Vj56Uw1k49UnAdIHieSZVQSkQNfoP1xtLtU6bHzol3QyK3MnpBTZvpROXM5cDUxe9MB7wMnOwqmf0WkciuTsAunLobX0L--Y_m-4uL5zr1EOEYXqwAKKuXma7_ienhJ1-g==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),           

        'qwen-coder-plus':
        ('BVTI59azmpbz_QfdY3F3Vj56Uw1k49UnAdIHieSZVQSkQNfoP1xtLtU6bHzol3QyK3MnpBTZvpROXM5cDUxe9MB7wMnOwqmf0WkciuTsAunLobX0L--Y_m-4uL5zr1EOEYXqwAKKuXma7_ienhJ1-g==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'qwen-long':
        ('BVTI59azmpbz_QfdY3F3Vj56Uw1k49UnAdIHieSZVQSkQNfoP1xtLtU6bHzol3QyK3MnpBTZvpROXM5cDUxe9MB7wMnOwqmf0WkciuTsAunLobX0L--Y_m-4uL5zr1EOEYXqwAKKuXma7_ienhJ1-g==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'qwen2.5-72b-instruct':
        ('7hHqypzAGvy24gaDeI7ap8iA9SHFMrcHTpa8mexAtGsvZJiXxeafkKDUH0tujkwgOcDpr_yxS3UvzfXArTFU7L7Lwg9iNTZTTnuqfujou19LzvlWEroxRl7kown5eXKdrVChFCmo8zY45epsOCYu9w==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'qwen-vl-max':
        ('BVTI59azmpbz_QfdY3F3Vj56Uw1k49UnAdIHieSZVQSkQNfoP1xtLtU6bHzol3QyK3MnpBTZvpROXM5cDUxe9MB7wMnOwqmf0WkciuTsAunLobX0L--Y_m-4uL5zr1EOEYXqwAKKuXma7_ienhJ1-g==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'qwen2-vl-72b-instruct':
        ('Dicll3WB9wsc6KVyYmdxaB7R5tT-SPgANcwiFIK9lh4x9q2dyIXRdNZcGCuF6MzKlCdb8rXZ4jWHwYIKPRYXmzybJWewDaSq4ZiL9nUMWLIrH8vsRpkkPS6ePjX_Z1EtD8M2z8KvEfWDjHJW4kSwIw==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'qvq-72b-preview':
        ('hzAAAg-PqkmfN-jARD5LZuZIBhaID1TAkJl3N-LbtggiDCg9tBmM-_WMgCu7-jjrPTKEQlfIMvBGtDL2FaWe22VeOHs6jDE9xZkKQBXQLBULf3sjN487dz3YT9Od29_jHJQENpF2pE0f-rwmcTEt1A==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'qwq-plus':
        ('7hHqypzAGvy24gaDeI7ap8iA9SHFMrcHTpa8mexAtGsvZJiXxeafkKDUH0tujkwgOcDpr_yxS3UvzfXArTFU7L7Lwg9iNTZTTnuqfujou19LzvlWEroxRl7kown5eXKdrVChFCmo8zY45epsOCYu9w==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),
        
        'doubao-pro-32k-241215':
        ('DK4XMijELnQn2gsfot-iJ9yr8JATE4ziNBDYiicKVR57amwXdecAXEF3uG0r7TWWZLqyY8lMRExo53QkOWCSwdaUiUJGyxMKj8VimPoO6Cf0IkZEciDhDatg_b7RCQC1tQyFRMv5mjLPDk25Lt9Kkw==', 'e4ecd34dbf7102325da165ea40425f541cf4a26e7e82ca7757af0288a6c2d298'),

        'doubao-pro-32k-240828':
        ('DK4XMijELnQn2gsfot-iJ9yr8JATE4ziNBDYiicKVR57amwXdecAXEF3uG0r7TWWZLqyY8lMRExo53QkOWCSwdaUiUJGyxMKj8VimPoO6Cf0IkZEciDhDatg_b7RCQC1tQyFRMv5mjLPDk25Lt9Kkw==', 'e4ecd34dbf7102325da165ea40425f541cf4a26e7e82ca7757af0288a6c2d298'),

        'doubao-pro-256k-241115':
        ('DK4XMijELnQn2gsfot-iJ9yr8JATE4ziNBDYiicKVR57amwXdecAXEF3uG0r7TWWZLqyY8lMRExo53QkOWCSwdaUiUJGyxMKj8VimPoO6Cf0IkZEciDhDatg_b7RCQC1tQyFRMv5mjLPDk25Lt9Kkw==', 'e4ecd34dbf7102325da165ea40425f541cf4a26e7e82ca7757af0288a6c2d298'),

        'doubao-pro-256k-240828':
        ('DK4XMijELnQn2gsfot-iJ9yr8JATE4ziNBDYiicKVR57amwXdecAXEF3uG0r7TWWZLqyY8lMRExo53QkOWCSwdaUiUJGyxMKj8VimPoO6Cf0IkZEciDhDatg_b7RCQC1tQyFRMv5mjLPDk25Lt9Kkw==', 'e4ecd34dbf7102325da165ea40425f541cf4a26e7e82ca7757af0288a6c2d298'),

        'deepseek-chat':
        ('fawM3lydRVR_ed7DLNnn-sDWUt4rZMA9kT0nQl4LUaH9yNDY6rx9hBb5Ma_KzAlCeRbqpfFZNuLABAmEGMTJb-8BOgHvWcwkoo4ewdpP9lp8EPwaGCqlo8HeiFvQaNNPg6unS5tfMVoHwfwZwjd3fA==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'deepseek-reasoner':
        ('fawM3lydRVR_ed7DLNnn-sDWUt4rZMA9kT0nQl4LUaH9yNDY6rx9hBb5Ma_KzAlCeRbqpfFZNuLABAmEGMTJb-8BOgHvWcwkoo4ewdpP9lp8EPwaGCqlo8HeiFvQaNNPg6unS5tfMVoHwfwZwjd3fA==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'moonshot-v1-8k':
        ('UdPOq_Hvo_cNWznuuPmf9IG-1QEub0uZyZWObZ_EM9ZnpHmz9C6kqR30S2SFPcfwjEVMz7Rbjx-ci86WO8jKDlWMFmeXjoRzN2qY3Lm7ArGUOlBO3uN1KlRbEoIfoot56FMJSKCerP4QbSHeUONHng==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'moonshot-v1-32k':
        ('UdPOq_Hvo_cNWznuuPmf9IG-1QEub0uZyZWObZ_EM9ZnpHmz9C6kqR30S2SFPcfwjEVMz7Rbjx-ci86WO8jKDlWMFmeXjoRzN2qY3Lm7ArGUOlBO3uN1KlRbEoIfoot56FMJSKCerP4QbSHeUONHng==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'moonshot-v1-128k':
        ('UdPOq_Hvo_cNWznuuPmf9IG-1QEub0uZyZWObZ_EM9ZnpHmz9C6kqR30S2SFPcfwjEVMz7Rbjx-ci86WO8jKDlWMFmeXjoRzN2qY3Lm7ArGUOlBO3uN1KlRbEoIfoot56FMJSKCerP4QbSHeUONHng==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'moonshot-v1-auto':
        ('UdPOq_Hvo_cNWznuuPmf9IG-1QEub0uZyZWObZ_EM9ZnpHmz9C6kqR30S2SFPcfwjEVMz7Rbjx-ci86WO8jKDlWMFmeXjoRzN2qY3Lm7ArGUOlBO3uN1KlRbEoIfoot56FMJSKCerP4QbSHeUONHng==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'moonshot-v1-8k-vision-preview':
        ('xyj6dNO7yOW9bT1mpF-pRtmzhkPAckyc2fDahJijrXrzjRsxAZeAONZO_V8zm2Y_6l5e-toVRD_ezQQHMrfDHbVPUUPO3h96ot14VD1w7krX9UJyhAMXULsXaW16_SV832y5bT-DbcCNhtpU7azI-BXNrTHrqCh6dLyhhOxMMb4=', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'kimi-k2-0711-preview':
        ('b7dgwwQ2Ydg6aEFu2sjf42_GwlavoyMWVY6YtwhYiIisqxNEQD2TXSKwJwdW3cNai-L7c3X8HmLlmm0L757VaIsPnUzsvD5GpwPYQBu0PAwaA3H49DkILYohSipzti_Yblnq8mepVX_sTJ6o0F518Q==', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'kimi-k2-thinking':
        ('qvDDtcwlWpnpMZnWOKlqLThY2dYUTleigiKAzFKZKEiEUQOYaCHkihLP1-VlNyq9wDB2VXxRZjTvJBLyvVbrr9ZUZ9hLJpBOzJk_L1CMWyRRcnjRTXE7fKDgnJzVqUkg4gOX_ypw2zr9xACOyVkqvQ==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'glm-4-plus':
        ('sV9hW55RAGczevchE24DUMOiTP9pTEijygA8iAu2gx4sbc5cN0nOvCPD0Xms37t1tL_rkAGLe4Bbx1b-r3E4CSc7KgRVjKrr33kc2hJHdRk22_4agFHyMd8o-dmW9788', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'glm-4-long':
        ('sV9hW55RAGczevchE24DUMOiTP9pTEijygA8iAu2gx4sbc5cN0nOvCPD0Xms37t1tL_rkAGLe4Bbx1b-r3E4CSc7KgRVjKrr33kc2hJHdRk22_4agFHyMd8o-dmW9788', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'glm-4.7':
        ('9dAig0ASm7aFwU_f7cVLwajLyYEjtzK6yeMF7bIukSdmLf5bPC9qgJ53TA5t7g_iD51Skdmr6Zr5m6qC3PngI0Mfq8_SvqbufU7kPpI74RBoGRE4JUQO0hQeHc_TT0zG', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'step-2-16k':
        ('Pwyl3gS5Dpw9oFMo9NTdvpCgY2H_JS29oDmEQyMct4ngS1qURCQa24NsGLgHoc5-N8WBlt4-_-cTH3SFo6e-Nr2op2KrfkHKTMPNioMDddc8E0ildumtkuVz2uLNHMRz', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),
        
        'step-1o-vision-32k':
        ('Pwyl3gS5Dpw9oFMo9NTdvpCgY2H_JS29oDmEQyMct4ngS1qURCQa24NsGLgHoc5-N8WBlt4-_-cTH3SFo6e-Nr2op2KrfkHKTMPNioMDddc8E0ildumtkuVz2uLNHMRz', 'd16686fd0c9b3cf55a9484b20079ef62667d2d3cf2e42545646e16082c052e1e'),

        'doubao-1-5-thinking-pro-250415':
        ('89C76LmCkcFEbNRY4lpL-mcZHw1CVM7gIfaNzskEAeAS0HIBzhSDyh_AT9f59-tI19mO0E5un6upHG7XpfmXIBhxitR1qotnby3g9OTcDF_uu3uOIGhLhoOJEKwtNJ0S0FpmcMbFdbEzPS8pGYGa6ba5M_fxbZJSFN63MV3UQSI=', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'o3-2025-04-16':
        ('2kSIWm4Eu7Iu6rD89s_TtWa6P57wBg3X-88qeMKXyyi-EGdHZQ6MXOZX2PV5PLe2qFGBPmHjEVffTKLmYqA_1yZIe12CX1t4hadsu55WXMddDYe2GZ-Zjs2IHbdAaV1hNAwGV8Yx-00coH0YHKCzeA==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'grok-3-beta':
        ('88M0kDekUT_-EjmlhwsWfx7pAFe3fubkNuKVY7djJFG9pfh2imsRdjSj_uLZXUUgqOTNi3pEA6-uxjGOKlQA-LIf3CqoD3f2WlzGBwSLf8rnj1DxCectjTbA5eJENHUAa_GqWMrMDyumXcV9DL-4Fg==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'gemini-2.5-pro-preview-05-06':
        ('o3CI6qipQ7wkAOEpltIGnUhEsCWmlzos88r9LIQZPthU4EC0L1Ka3MituPnuzsrRNLR30heXMD_Cich8liHr1fiUxF6ZJSiBfgb2-FN4-u5asf55U2n-BvHQ9TgduKumVKimy0Uj9Xkad_coJiWrZQovv4QKq_RyeM2Y1SJ90Qs=', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'gemini-2.5-pro-preview-06-05':
        ('S1SEtjLAShceICPcSs5LZH37M-KK1KVMs_lP5em1aIY8WJCFfqZ1kSYbL3BkOZpwdOk0SU3zY3KToofbueCnCe9mUJT2QBZY1t_zYJqB7dVq10wZwBTiqEB3looUvML5SJUyOcphtjMKAojBl3VEUS0yn7rBlHzc-LiUs07dKu4=', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'claude-opus-4-20250514':
        ('9KtlPFjHUxmTEiKONb7CyESy4zBbF4jqJfGdjSsFsovLxahyDQyP7kel0IIlGD6I5f-e_DXbBbvz7EstA-X7_8ofDcP8KdVC_7ek_4m3gz_51D9z3Ixz5CV7zzShASWp9PVI7BYGBr_6lfnEheL3AA==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'gpt-5-2025-08-07':
        ('6oh_brJA7rCLhE0Sg8QmW_rK8N01e7gBPavoLbzpXOXOIDlBVo6DvJ1Rb-f3_zfNNwv_prS9gSJzmxhoCEwSMvRT53FcIA0XOZh6yQSa-CsRef1B9VcKxYDrAX9cKgTSldclNAmcm395ZeTKfH4ZtQ==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'claude-sonnet-4-5-20250929':
        ('cPwdC0_PzFJbq1futpFks36mVg1KdhZZ56tc000KrgISNPYGGjUhiB1pwUGcc621wMXomt0VaMQEi0Rgg6om8YSuAUwd2_HyhimvWozrjr2X-0Fkq1eap3KVCYUIkPO4tfTum1V06HorEh_DfB4PtpOA2p0V5aAFF2eust6I0rI=', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),

        'gemini-3-pro-preview': # gemini 原生格式
        ('VAm0udzlBIw1C5_ynbpG_o7419_u2f4f9VyKfrj6bU3oLuCzbCAht8B4Q_EdPgPuufIZYOxAlPwZgUZ3krEBD-3VjFKlpDeqFK3GMzyHZQLGqnuEL93qYlXeIBZg9LiQqBdmIv0E011Tr8TWku60Sg==', '610e4bc50a3c533b5401370fe126b36741872487460328603007d0c014158740'),
        }
        
    minimax_token = model_map_token[model_version_proxy][0]
    billing_token = model_map_token[model_version_proxy][1]

    if minimax_token.startswith("ijJMhfgR0fX68dDYi9TjJjY3h5fDo1J3rFqv") and model_version_proxy.startswith('o1-preview'):
        model_version_proxy = 'o1-preview'
    elif minimax_token.startswith("gYqF0z5MT6xB5HByEgW8wwW1XRx8-rUw1fZ1Iztx") and model_version_proxy.startswith('o1-preview'):
        model_version_proxy = "o1-preview-2024-09-12"

    # Call API
    url = "http://thirdpart-proxy-prod.xaminim.com/v1/proxy"
    headers = {"Content-Type": "application/json;", "minimax_token": minimax_token, "billing_token": billing_token,
               "Accept-Encoding": "deflate"}
    if "gemini" in model_version_proxy and model_version_proxy != 'gemini-2.5-pro-preview-03-25':
        new_messages = []
        system_setting = ""
        for m in messages:
            role = m['role']
            if role in ['user', 'ai']:
                if role == 'ai':
                    role = 'model'
                new_messages.append({"role":role, "parts":[{"text":m['content']}]})
            elif role == 'system':
                system_setting = m['content']
        if system_setting != "":
            data = {"model": model_version_proxy, "contents":new_messages, "system_instruction":{"parts":[{"text":system_setting}]}, "generationConfig":{"temperature": temperature, "maxOutputTokens": max_tokens, "thinkingConfig": {"includeThoughts": True}}}
        else:
            data = {"model": model_version_proxy, "contents":new_messages, "generationConfig":{"temperature": temperature, "maxOutputTokens": max_tokens, "thinkingConfig": {"includeThoughts": True}}}
    elif "claude" in model_version_proxy:
        if model_version_proxy.startswith("claude-3-7") or model_version_proxy.startswith("claude-opus-4"):
            data = {
                "model": model_version_proxy,
                "messages": messages,
                "thinking": {"type": "enabled", "budget_tokens": 1024},
                "max_tokens": max_tokens,
            }
        else:
            new_messages = []
            for m in messages:
                role = m['role']
                if role in ['user', 'ai', 'system']:
                    if role == 'ai':
                        role = 'assistant'
                    new_messages.append({"role":role, "content":m['content']})
            data = {"model": model_version_proxy, "messages": new_messages, "temperature": temperature, "max_tokens": max_tokens} 
    
    elif model_version_proxy in ['o1-preview', 'o1-mini', 'o1-preview-2024-09-12', 'o1-mini-2024-09-12']:
        messages = messages[-1:]
        data = {"model": model_version_proxy, "messages": messages, "stream": False,
                "max_completion_tokens": min(max_tokens, 32000)}
    
    elif model_version_proxy in ['o3-mini', 'o1-2024-12-17','o3-2025-04-16']:
        new_messages = []
        for m in messages:
            if m['role'] == 'system':
                m['role'] = 'developer' 
            new_messages.append(m)
        data = {"model": model_version_proxy, "messages": new_messages, "stream": False,
                "reasoning_effort": reasoning_effort, #"temperature": temperature,
                "max_completion_tokens": min(max_tokens, 100000), "n": 1}
    
    elif 'glm' in model_version_proxy:
        data = {"model": model_version_proxy, "messages": messages, "temperature": temperature, "stream": False}
    
    elif "doubao" in model_version_proxy:
        data = {"model": doubao_model_name_to_ep[model_version_proxy], "messages": messages, "stream": False, "temperature": temperature,
                "max_tokens": max_tokens}
    
    elif "gpt-5" in model_version_proxy:
        data = {"model": model_version_proxy, "messages": messages, "stream": False, "temperature": temperature,
                "max_completion_tokens": min(max_tokens + 2048, 32000)}
    
    else:
        data = {"model": model_version_proxy, "messages": messages, "stream": False, "temperature": temperature,
                "max_tokens": max_tokens}

    if response_format == 'json' and '4o' in model_version:
        data["response_format"] = {"type": "json_object"}
    # 429 限流
    current_second = int(time.time())
    response_429_count = 0
    for attempt in range(1, max_try + 1):
        now_second = int(time.time())
        if now_second >= current_second + 1:
            current_second = now_second
            response_429_count = 0  # 重置计数

        time_start = time.time()
        try:
            if debug:
                print("--headers--", headers)
                print("--data--", data)
            response = requests.post(url, headers=headers, json=data, timeout=350)
            time_end = time.time()
            if debug:
                print("--response--")
                print(response.text)
                print(f"Time taken: {time_end - time_start} seconds")

            if response.status_code in [429, 501]:
                response_429_count += 1
                print(f"Attempt {attempt}: {response.status_code}. Count in current second: {response_429_count}")
                    
                # 1s内5次429
                if response_429_count >= 5: # 5 times in 1s
                    sleep_time = 2 ** (np.random.uniform(min(response_429_count / 5, 2), 3.2))
                    print(f"Sleeping for {sleep_time} seconds")
                else:
                    random_noise = max(np.random.randn() * 0.2, 0)
                    sleep_time = 2 ** (response_429_count - 4.1) + random_noise
                    print(f"Sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)
            else:
                if "gemini" in model_version_proxy and model_version_proxy != 'gemini-2.5-pro-preview-03-25': 
                    response_dict = json.loads(response.text)['candidates'][0]
                    if response_dict.get('finishReason', 'STOP') == "STOP":
                        if len(response_dict['content']['parts']) > 1 and response_dict['content']['parts'][0].get('thought', False) is True:
                            thinking_text = response_dict['content']['parts'][0]['text']
                            response_text = response_dict['content']['parts'][1]['text']
                        else:
                            thinking_text = ""
                            response_text = response_dict['content']['parts'][0]['text']
                        if thinking_text:
                            response_text = "<think>" + thinking_text + "</think>\n" + response_text
                        assert response_text
                        return response_text
                    elif response_dict.get("finishReason", "STOP") == "SAFETY":
                        return "SAFETY ERROR"
                    elif "promptFeedback" in response_dict:
                        return "BLOCK ERROR"
                    else:
                        return "OTHER ERROR"
                elif "claude" in model_version_proxy: 
                    try:
                        response_dict = json.loads(response.text)['content'][0]
                        if model_version_proxy != "claude-3-7-sonnet-20250219":
                            if response_dict.get('stop_reason', 'end_turn') == "end_turn":
                                response_text = response_dict['text']
                                assert response_text
                                return response_text
                    except:
                        response_dict = json.loads(response.text)['choices'][0]
                        if response_dict.get('finish_reason', 'stop') == "stop":
                            response_text = response_dict['message']['content']
                            if 'resoning_content' in response_text:
                                response_text = response_text['resoning_content']
                            assert response_text
                            return response_text
                else: 
                    response_dict = json.loads(response.text)
                    if "error" in response_dict:
                        if response_dict["error"].get("type", "") == "invalid_request_error" and response_dict["error"].get("code", "") == "invalid_prompt":
                            print(f"Invalid prompt: {response.text}")
                            return None
                        if response_dict["error"].get("type", "") == "insufficient_quota" and response_dict["error"].get("code", "") == "insufficient_quota":
                            print(f"Insufficient quota: {response.text}")
                            return None
                    response_dict = response_dict['choices'][0]
                    if response_dict.get('finish_reason', 'stop') == "stop":
                        response_text = response_dict['message']['content']
                        assert response_text
                        return response_text
        except Exception as e:
            print(f"*** 模型 {model_version_proxy} 发生错误，minimax token: '{minimax_token}'，在 AI 数据获取群 @庚辰 反馈 ***")
            try:
                print(f'Status code: {response.status_code}, Response: {response.text}')
            except NameError:
                print(f'Request failed before response was received')
            print(f"GPT call failed: {e},  retrying...")
            random_noise = np.random.randn() * 0.2
            sleep_time = 2 ** (np.random.uniform(attempt/max_try, 3.5)) + random_noise
            time.sleep(sleep_time)
    try:
        print(f"GPT_CALL FAILED MINIMAX: max_try exceeded, data: {data}, response: {response.text}")
    except NameError:
        print(f"GPT_CALL FAILED MINIMAX: max_try exceeded, data: {data}, no response received")
    return None
    

def get_batch_gpt_responses(messages_list, model_version, temperature=0.0, max_tokens=4096, max_try=100, max_workers=5, response_format=''):
    """Get response from GPT model using minimax API
    Args:
        messages_list (list): list of messages, where each message is a list of dict with keys 'role' and 'content', e.g.: [{'role': 'system', 'content': 'You are a
        helpful assistant.'}, {'role': 'user', 'content': '1+1和1*1哪个大'}]
        model_version (str): model version to use: 'gpt-4-1106-preview', 'gpt-4-32k-0613', 'gpt-4-turbo-2024-04-09',
        'gpt-4o-2024-05-13'
        temperature (float): sampling temperature: less than 2.0
        max_tokens (int): maximum number of tokens to generate: less than 4096
        max_try (int): maximum number of tries to call the API
        max_workers (int): maximum number of workers used concurrently
    Returns:
        str: response text
    """
    def perform_request(msg, index):
        response_content = get_gpt_response(msg, model_version, temperature, max_tokens, max_try, response_format=response_format)
        msg += [{"role": "assistant", "content": response_content}]
        return index, msg

    res = [None] * len(messages_list)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = [executor.submit(perform_request, msg, index) for index, msg in
                           enumerate(messages_list)]
        completed = 0
        for future in as_completed(future_to_index):
            index, result = future.result()
            completed += 1  # 更新完成的任务数
            print(f"Progress: {completed}/{len(messages_list)} tasks completed.", flush=True)  # 打印进度
            if result is not None:
                res[index] = result
    return res

def construct_messages(model, prompt, sys_prompt, image_url=None):
        if model not in vision_models:
            messages = [
                #{'role': 'system', 'content': sys_prompt}, 
                {'role': 'user', 'content': prompt}, 
            ]

        else:
            if model == 'moonshot-v1-8k-vision-preview':
                image_path = "/minimax-dialogue/users/puwang/geld/test_input/test_image_2.png"
                with open(image_path, "rb") as f:
                    image_data = f.read()
                image_url = f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
            else:
                image_url = "https://img.tukuppt.com/ad_preview/00/17/33/5c99ce064a68f.jpg!/fw/980"
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        },
                        {
                            "type": "text",
                            "text": "图片里有什么"
                        }
                    ]
                }
            ]
        return messages
    
if __name__ == '__main__':
    prompt = "你好, 你是什么模型? 你是什么时候训练的，有多少参数？你知道 minimax m1 吗？"
    sys_prompt = "You are a helpful assistant."


    # 单次调用
    models = ['glm-4.7', 'kimi-k2-thinking']
    max_tokens = 4096
    temperature = 0.1

    for m in models:
        print(f'\n\n{m}, max tokens {max_tokens}, test case:')
        messages = construct_messages(m, prompt, sys_prompt)
        print(get_gpt_response(messages, m, max_tokens=max_tokens, temperature=temperature, debug=True))
    
    # 批量调用
    # start_time = time.time()
    # for m in models:
    #     print(f'\n\n{m}, max tokens {max_tokens}, test case:')
    #     with ThreadPoolExecutor(max_workers=1) as executor:
    #         future_to_index = [executor.submit(get_4_call, "1 + 1和 1 * 1 哪个大", m, max_tokens=max_tokens) for i in range(20)]
    #         for future in as_completed(future_to_index):
    #             result = future.result()
    #             print(result[:10])
    #             #time.sleep(0.5)
    # print(time.time() - start_time)