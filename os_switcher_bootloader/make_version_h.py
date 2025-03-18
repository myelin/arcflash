import datetime

now = datetime.datetime.now()

print(f'''#define ARCFLASH_BUILD_DATE "{now.strftime('%Y-%m-%d')}"''')
