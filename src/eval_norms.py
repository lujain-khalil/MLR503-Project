import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from utils import SUPPORTED_MODELS, GREEN, PURPLE, PALLETE, compute_norm, check_normality, perform_statistical_test
import os 
import json

parser = argparse.ArgumentParser(description="Evaluate embeddings using a specified multilingual masked LLM.")
parser.add_argument('model_name', type=str, choices=SUPPORTED_MODELS.keys(), help="Name of the model to use (e.g., 'xlm-roberta-base', 'mbert', 'gigabert')")

args = parser.parse_args()
MODEL_NAME = args.model_name

results_dir = f"results/{MODEL_NAME}/norms/"
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

# Load the generated embeddings for cultural terms
embeddings_df = pd.read_pickle(f"embeddings/{MODEL_NAME}/culture_term_embeddings.pkl")

# Separate embeddings based on culture (Arab vs. Western)
arab_embeddings = embeddings_df[embeddings_df['culture'] == 'Arab']['embedding'].values
western_embeddings = embeddings_df[embeddings_df['culture'] == 'Western']['embedding'].values

# Compute norms for Arab and Western embeddings
arab_norms = np.array([compute_norm(embedding) for embedding in arab_embeddings])
western_norms = np.array([compute_norm(embedding) for embedding in western_embeddings])

# Calculate the mean and standard deviation of the norms for each group
arab_mean_norm = np.mean(arab_norms)
western_mean_norm = np.mean(western_norms)
arab_std_norm = np.std(arab_norms)
western_std_norm = np.std(western_norms)

mean_std_values = {
    'Arab': {'mean': float(arab_mean_norm), 'std': float(arab_std_norm)},
    'Western': {'mean': float(western_mean_norm), 'std': float(western_std_norm)}
}

result_data = {'mean_std_values': mean_std_values}

# Prepare data for boxplot, violin plot, and histogram
norms_df = pd.DataFrame({
    'Culture': ['Arab'] * len(arab_norms) + ['Western'] * len(western_norms),
    'Norm': np.concatenate([arab_norms, western_norms])
})

# Boxplot
plt.figure(figsize=(8, 6))
sns.boxplot(data=norms_df, x='Culture', y='Norm', hue='Culture', legend=False, palette=PALLETE)
plt.title(f'Distribution of Norms: Arab vs Western Terms ({MODEL_NAME})')
plt.xlabel('Cultural Group')
plt.ylabel('Embedding Norm')
plt.tight_layout()
plt.savefig(f"{results_dir}boxplot_norms.png")
plt.close()

# Violin Plot
plt.figure(figsize=(8, 6))
sns.violinplot(data=norms_df, x='Culture', y='Norm', hue='Culture', legend=False, palette=PALLETE)
plt.title(f'Distribution of Norms: Arab vs Western Terms ({MODEL_NAME})')
plt.xlabel('Cultural Group')
plt.ylabel('Embedding Norm')
plt.tight_layout()
plt.savefig(f"{results_dir}violin_plot_norms.png")
plt.close()

# Histogram with KDE
plt.figure(figsize=(8, 6))
sns.histplot(arab_norms, kde=True, color=GREEN, label='Arab', stat='density', bins=20, alpha=0.5)
sns.histplot(western_norms, kde=True, color=PURPLE, label='Western', stat='density', bins=20, alpha=0.5)
plt.title(f'Norm Distribution with KDE: Arab vs Western Terms ({MODEL_NAME})')
plt.xlabel('Embedding Norm')
plt.ylabel('Density')
plt.legend()
plt.tight_layout()
plt.savefig(f"{results_dir}histogram_kde_norms.png")
plt.close()

# CDF Plot
plt.figure(figsize=(8, 6))
sns.ecdfplot(arab_norms, color=GREEN, label='Arab', linewidth=2)
sns.ecdfplot(western_norms, color=PURPLE, label='Western', linewidth=2)
plt.title(f'CDF of Norms: Arab vs Western Terms {MODEL_NAME}')
plt.xlabel('Embedding Norm')
plt.ylabel('CDF')
plt.legend()
plt.tight_layout()
plt.savefig(f"{results_dir}cdf_norms.png")
plt.close()

# Comparision of cultural entities
culture_entity_df = embeddings_df.copy()
culture_entity_df['Norm'] = culture_entity_df['embedding'].apply(compute_norm)

# Calculate mean and std for each culture-entity
culture_entity_stats = culture_entity_df.groupby(['culture', 'entity'])['Norm'].agg(['mean', 'std']).reset_index()
result_data['culture_entity_stats'] = culture_entity_stats.to_dict(orient='records')

with open(f"{results_dir}mean_std_values.json", 'w') as json_file:
    json.dump(result_data, json_file, indent=4)

plt.figure(figsize=(15, 6))
barplot = sns.barplot(data=culture_entity_stats, x='entity', y='mean', hue='culture', palette=PALLETE)
for container in barplot.containers:
    barplot.bar_label(container, fmt='%.2f', padding=3)
plt.title(f'Mean Embedding Norms by Culture and Entity ({MODEL_NAME})')
plt.xlabel('Entity')
plt.ylabel('Mean Norm')
plt.tight_layout()
plt.savefig(f"{results_dir}culture_entity_comparison.png")

print(f"All visualizations for {MODEL_NAME} have been saved in '{results_dir}' directory.")

# Check normality for Arab and Western norms
arab_normality = check_normality(arab_norms)
western_normality = check_normality(western_norms)

# Perform statistical test based on normality results
statistical_results = perform_statistical_test(arab_norms, western_norms, arab_normality, western_normality)

# Combine all results
results = {
    'normality_tests': {
        'Arab': arab_normality,
        'Western': western_normality
    },
    'statistical_tests': statistical_results
}

with open(f"{results_dir}statistical_tests.json", 'w') as json_file:
    json.dump(results, json_file, indent=4)

print(f"Results saved in '{results_dir}statistical_tests.json'")
