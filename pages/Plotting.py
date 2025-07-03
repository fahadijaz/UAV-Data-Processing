import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

data = ("24BPROBARG20_Vollebekk_2024.xlsx")

# Exploring the data
def read_data(file_path):
    df = pd.read_excel(file_path)
    print("This is the full dataframe")
    print(df)
    print("\nThe first 5 rows of data")
    print(df.head)
    print("\nLast 5 rows of data")
    print(df.tail)
    return df

df = read_data(data)

# Checking for missing values
def missing_values(df):
    total_missing_values = df.isnull().sum().sum()
    if total_missing_values > 0:
        print(f"There are {total_missing_values} missing values")
        raise ValueError("There are missing values")
    else:
        print("There are no missing values :)")

missing_values(df)

# Velg hvilke statistiske kolonner som skal visualiseres
statistical_features = ['max', 'mean', 'median', 'min', 'std', 'variance', 'kurtosis', 'skewness']

# Filtrer for ett spektrum, f.eks. 'NDVI'
selected_spectrum = 'NDVI'
filtered_df = df[df['Spectrum'] == selected_spectrum]

# Begrens til dato og statistiske kolonner
plot_df = filtered_df[['date'] + statistical_features]

import matplotlib.pyplot as plt

# Plot for each feature
for feature in statistical_features:
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'{feature.upper()} - Visualiseringer for {selected_spectrum}', fontsize=16)
    
    # Boxplot
    sns.boxplot(data=plot_df, x='date', y=feature, ax=axs[0, 0])
    axs[0, 0].set_title('Boxplot')
    
    # Violin plot
    sns.violinplot(data=plot_df, x='date', y=feature, ax=axs[0, 1])
    axs[0, 1].set_title('Violinplot')
    
    # Histogram
    sns.histplot(data=plot_df, x=feature, kde=True, ax=axs[1, 0])
    axs[1, 0].set_title('Histogram')
    
    # Scatter plot
    sns.scatterplot(data=plot_df, x='date', y=feature, ax=axs[1, 1])
    axs[1, 1].set_title('Scatterplot')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
