import requests
r = requests.get('http://127.0.0.1:5001/revisao-categorias')
print('STATUS', r.status_code)
print(r.text[:2000])
with open('debug_revisao.html','w',encoding='utf-8') as f:
    f.write(r.text)
print('\nSaved full HTML to debug_revisao.html')