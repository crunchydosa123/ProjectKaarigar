  from google import genai
  from google.genai import types

  with open('D:\projects\Anuj_Portfolio\portfolio_anuj_tadkase\src\assets\empty_marauders_map.jpg', 'rb') as f:
      image_bytes = f.read()

  client = genai.Client(api_key="AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4")
  response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
      types.Part.from_bytes(
        data=image_bytes,
        mime_type='image/jpeg',
      ),
      'Caption this image.'
    ]
  )

  print(response.text)