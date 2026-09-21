import pandas as pd

#Создание DataFrame
df = pd.DataFrame({
    'Col1': ["C", "D", "B", "A", "A", "B", "C", "A", "A"],
    'Col2': range(1, 10),
    'Col3': pd.NA,
})

#Выборка и замена букв А с значением TRUE через булеву маску + векторизацию
mask = df['Col1'] == "A"
idx = df.index[mask][:2]
df.loc[idx, 'Col3'] = True

print (df)