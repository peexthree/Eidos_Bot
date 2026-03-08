with open('test_script.py', 'r') as f:
    content = f.read()

content = content.replace(
    'initDataUnsafe: { user: { id: 12345 } },',
    'initDataUnsafe: { user: { id: 12345 } },\n                    initData: "query_id=mock_12345&user=%7B%22id%22%3A12345%7D",'
)

with open('test_script.py', 'w') as f:
    f.write(content)
