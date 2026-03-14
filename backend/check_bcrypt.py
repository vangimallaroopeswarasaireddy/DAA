import bcrypt
print('version', bcrypt.__version__)
print('__about__ attribute present?', hasattr(bcrypt,'__about__'))
print('about:', getattr(bcrypt,'__about__', None))
