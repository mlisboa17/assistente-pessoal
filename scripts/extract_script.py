from bs4 import BeautifulSoup
html = open('debug_revisao.html','r',encoding='utf-8').read()
soup = BeautifulSoup(html,'html.parser')
scripts = soup.find_all('script')
print('Found',len(scripts),'script tags')
# Find the script which contains our log
for i, s in enumerate(scripts):
    if s.string and 'revisao_categorias script loaded' in s.string:
        print('Index',i)
        script_content = s.string
        with open('debug_revisao_script.js','w',encoding='utf-8') as f:
            f.write(script_content)
        print('Wrote debug_revisao_script.js')
        break
else:
    print('Script not found')
