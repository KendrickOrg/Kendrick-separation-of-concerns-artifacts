import sys, asyncio
from playwright.async_api import async_playwright
async def main(src, dst):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto('file://' + src)
        # size the page to its content so the PDF is a single, tightly cropped page
        w = await pg.evaluate("Math.max(...[...document.querySelectorAll('.col, .legend')].map(e => { const r=document.createRange(); r.selectNodeContents(e); return r.getBoundingClientRect(); }).map(r => r.right))")
        h = await pg.evaluate('document.body.scrollHeight')
        await pg.set_viewport_size({'width': int(w) + 40, 'height': int(h) + 40})
        await pg.add_style_tag(content=f'@page {{ size: {int(w)+46}px {int(h)+46}px; margin: 6mm; }}')
        await pg.pdf(path=dst, print_background=True, prefer_css_page_size=True)
        await b.close()
asyncio.run(main(sys.argv[1], sys.argv[2]))
