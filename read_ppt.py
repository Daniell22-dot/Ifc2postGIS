from pptx import Presentation
prs = Presentation('D:\ifc2postgis_reports\ifc2postgis_presentation.pptx')
print(f'Total slides: {len(prs.slides)}')
for i, slide in enumerate(prs.slides):
    shapes = slide.shapes
    print(f'Slide {i+1}: {len(shapes)} shapes')
    for j, shape in enumerate(shapes):
        if hasattr(shape, 'text') and shape.text:
            text = shape.text[:80] + '...' if len(shape.text) > 80 else shape.text
            print(f'  Shape {j}: text = "{text}"')
        elif hasattr(shape, 'image'):
            print(f'  Shape {j}: image (size={shape.image.width}x{shape.image.height})')