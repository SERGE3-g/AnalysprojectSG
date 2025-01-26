import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, learning_curve
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder, PolynomialFeatures
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_curve, auc, \
    precision_recall_curve
from sklearn.inspection import permutation_importance
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from scipy import stats
from datetime import datetime, timedelta
import warnings
import joblib
import json
import logging

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('churn_analysis.log'),
        logging.StreamHandler()
    ]
)


class ChurnAnalyzer:
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.poly_features = PolynomialFeatures(degree=2, include_bias=False)
        self.pca = PCA(n_components=0.95)
        self.model = None
        self.feature_importance = None
        self.kmeans = None
        self.customer_segments = None
        self.feature_names = None
        logging.info("ChurnAnalyzer initialized")

    def generate_mock_data(self, num_samples=1000):
        np.random.seed(self.random_state)

        # Generate current date and customer join dates
        current_date = datetime.now()
        join_dates = [current_date - timedelta(days=np.random.randint(1, 1825))
                      for _ in range(num_samples)]

        # Demographics
        age = np.random.normal(45, 15, num_samples).clip(18, 90)
        gender = np.random.choice(['Male', 'Female', 'Other'], num_samples, p=[0.48, 0.48, 0.04])
        income = np.random.lognormal(10.5, 0.5, num_samples).clip(20000, 200000)
        education = np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], num_samples)
        location = np.random.choice(['Urban', 'Suburban', 'Rural'], num_samples, p=[0.45, 0.35, 0.20])

        # Purchase History
        total_purchases = np.random.negative_binomial(10, 0.5, num_samples)
        avg_purchase_value = np.random.gamma(shape=2, scale=100, size=num_samples)
        days_since_last_purchase = np.random.exponential(50, num_samples).clip(1, 365)
        purchase_frequency = np.random.gamma(shape=2, scale=0.5, size=num_samples)

        # Product Usage
        products_owned = np.random.poisson(lam=2, size=num_samples) + 1
        premium_features = np.random.choice([0, 1], num_samples, p=[0.7, 0.3])
        usage_frequency = np.random.gamma(shape=2, scale=2, size=num_samples)

        # Customer Service
        support_calls = np.random.poisson(lam=2, size=num_samples)
        complaints = np.random.poisson(lam=0.5, size=num_samples)
        resolved_complaints = np.minimum(complaints, np.random.binomial(n=complaints, p=0.8))

        # Digital Engagement
        website_visits = np.random.negative_binomial(5, 0.5, num_samples)
        mobile_app_usage = np.random.choice([0, 1], num_samples, p=[0.4, 0.6])
        email_engagement = np.random.beta(2, 5, num_samples)
        social_media_engagement = np.random.beta(1.5, 5, num_samples)

        # Satisfaction Metrics
        satisfaction_score = np.random.normal(7.5, 1.5, num_samples).clip(1, 10)
        nps_score = np.random.normal(50, 20, num_samples).clip(0, 100)

        # Calculate churn probability based on various factors
        churn_probability = 1 / (1 + np.exp(-(
                -3  # base probability
                + 0.03 * (age - 45) / 15  # age factor
                - 0.4 * (satisfaction_score - 7.5) / 1.5  # satisfaction factor
                + 0.3 * (days_since_last_purchase / 365)  # recency factor
                - 0.2 * (total_purchases / 10)  # purchase history factor
                - 0.3 * (usage_frequency / 2)  # usage factor
                + 0.4 * (complaints / 0.5)  # complaint factor
                - 0.2 * (website_visits / 5)  # engagement factor
                - 0.3 * premium_features  # premium status factor
        )))

        # Generate churn based on probability
        churn = np.random.binomial(1, churn_probability)

        # Create DataFrame
        data = pd.DataFrame({
            'JoinDate': join_dates,
            'Age': age,
            'Gender': gender,
            'Income': income,
            'Education': education,
            'Location': location,
            'TotalPurchases': total_purchases,
            'AvgPurchaseValue': avg_purchase_value,
            'DaysSinceLastPurchase': days_since_last_purchase,
            'PurchaseFrequency': purchase_frequency,
            'ProductsOwned': products_owned,
            'PremiumFeatures': premium_features,
            'UsageFrequency': usage_frequency,
            'SupportCalls': support_calls,
            'Complaints': complaints,
            'ResolvedComplaints': resolved_complaints,
            'WebsiteVisits': website_visits,
            'MobileAppUsage': mobile_app_usage,
            'EmailEngagement': email_engagement,
            'SocialMediaEngagement': social_media_engagement,
            'SatisfactionScore': satisfaction_score,
            'NPSScore': nps_score,
            'Churn': churn
        })

        # Add derived features
        data['CustomerAge'] = (current_date - pd.to_datetime(data['JoinDate'])).dt.days / 365
        data['ComplaintResolutionRate'] = np.where(data['Complaints'] > 0,
                                                   data['ResolvedComplaints'] / data['Complaints'],
                                                   1)
        data['DigitalEngagementScore'] = (data['WebsiteVisits'] * 0.3 +
                                          data['MobileAppUsage'] * 0.3 +
                                          data['EmailEngagement'] * 0.2 +
                                          data['SocialMediaEngagement'] * 0.2)

        logging.info(f"Generated mock data with {num_samples} samples")
        return data

    def preprocess_data(self, data):
        processed_data = data.copy()

        # Handle missing values
        for col in processed_data.columns:
            if processed_data[col].dtype in ['int64', 'float64']:
                processed_data[col].fillna(processed_data[col].median(), inplace=True)
            else:
                processed_data[col].fillna(processed_data[col].mode()[0], inplace=True)

        # Encode categorical variables
        categorical_columns = processed_data.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if col != 'JoinDate':
                processed_data[col] = self.label_encoder.fit_transform(processed_data[col])

        # Handle dates
        if 'JoinDate' in processed_data.columns:
            processed_data['JoinDate'] = pd.to_datetime(processed_data['JoinDate'])
            processed_data['DaysSinceJoining'] = (datetime.now() - processed_data['JoinDate']).dt.days
            processed_data.drop('JoinDate', axis=1, inplace=True)

        # Handle outliers using IQR method
        def handle_outliers(df, column):
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df[column] = df[column].clip(lower_bound, upper_bound)
            return df

        numeric_columns = processed_data.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_columns:
            if col != 'Churn':
                processed_data = handle_outliers(processed_data, col)

        # Create interaction features
        processed_data['ValueFrequency'] = processed_data['AvgPurchaseValue'] * processed_data['PurchaseFrequency']
        processed_data['SatisfactionRetention'] = processed_data['SatisfactionScore'] * processed_data['CustomerAge']
        processed_data['EngagementValue'] = processed_data['DigitalEngagementScore'] * processed_data[
            'AvgPurchaseValue']

        # Add polynomial features for key metrics
        poly_columns = ['SatisfactionScore', 'AvgPurchaseValue', 'UsageFrequency']
        poly_features = self.poly_features.fit_transform(processed_data[poly_columns])
        poly_feature_names = [f'Poly_{i}' for i in range(poly_features.shape[1])]
        processed_data = pd.concat([
            processed_data,
            pd.DataFrame(poly_features[:, len(poly_columns):],
                         columns=poly_feature_names[len(poly_columns):])
        ], axis=1)

        # Scale features
        features_to_scale = processed_data.columns.difference(['Churn'])
        processed_data[features_to_scale] = self.scaler.fit_transform(processed_data[features_to_scale])

        # Perform PCA
        pca_features = self.pca.fit_transform(processed_data[features_to_scale])
        pca_columns = [f'PCA_{i}' for i in range(pca_features.shape[1])]
        processed_data = pd.concat([
            processed_data,
            pd.DataFrame(pca_features, columns=pca_columns)
        ], axis=1)

        # Store feature names
        self.feature_names = processed_data.columns.tolist()

        logging.info("Data preprocessing completed")
        return processed_data

    def perform_customer_segmentation(self, data):
        # Select features for segmentation
        segmentation_features = [
            'AvgPurchaseValue', 'PurchaseFrequency', 'ProductsOwned',
            'UsageFrequency', 'DigitalEngagementScore', 'SatisfactionScore'
        ]

        # Scale features
        scaled_features = self.scaler.fit_transform(data[segmentation_features])

        # Determine optimal number of clusters using elbow method
        inertias = []
        K = range(2, 11)
        for k in K:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state)
            kmeans.fit(scaled_features)
            inertias.append(kmeans.inertia_)

        # Find elbow point
        diffs = np.diff(inertias)
        elbow_point = np.argmin(diffs) + 2

        # Perform final clustering
        self.kmeans = KMeans(n_clusters=elbow_point, random_state=self.random_state)
        self.customer_segments = self.kmeans.fit_predict(scaled_features)

        # Add segment information to data
        segment_profiles = []
        for i in range(elbow_point):
            segment_mask = (self.customer_segments == i)
            segment_data = data[segment_mask]

            profile = {
                'segment_id': i,
                'size': segment_mask.sum(),
                'avg_value': segment_data['AvgPurchaseValue'].mean(),
                'avg_frequency': segment_data['PurchaseFrequency'].mean(),
                'avg_satisfaction': segment_data['SatisfactionScore'].mean(),
                'churn_rate': segment_data['Churn'].mean()
            }
            segment_profiles.append(profile)

        self.segment_profiles = pd.DataFrame(segment_profiles)
        logging.info(f"Customer segmentation completed with {elbow_point} segments")
        return self.customer_segments

    def train_model(self, X_train, y_train):
        # Create base models
        rf_model = RandomForestClassifier(random_state=self.random_state)
        gb_model = GradientBoostingClassifier(random_state=self.random_state)

        # Define parameter grids
        rf_param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 20, 30, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2']
        }

        gb_param_grid = {
            'n_estimators': [100, 200, 300],
            'learning_rate': [0.01, 0.1, 0.3],
            'max_depth': [3, 5, 7],
            'min_samples_split': [2, 5, 10],
            'subsample': [0.8, 0.9, 1.0]
        }

        # Train models with GridSearchCV
        rf_grid = GridSearchCV(
            rf_model,
            rf_param_grid,
            cv=5,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=1
        )

        gb_grid = GridSearchCV(
            gb_model,
            gb_param_grid,
            cv=5,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=1
        )

        logging.info("Starting model training...")
        rf_grid.fit(X_train, y_train)
        gb_grid.fit(X_train, y_train)

        # Select best model
        if rf_grid.best_score_ > gb_grid.best_score_:
            self.model = rf_grid
            logging.info("Random Forest selected as best model")
        else:
            self.model = gb_grid
            logging.info("Gradient Boosting selected as best model")

        # Calculate feature importance
        self.feature_importance = self.calculate_feature_importance(X_train,y_train)

        logging.info("Model training completed")

    def calculate_feature_importance(self, X, y):
            # Calculate permutation importance
            perm_importance = permutation_importance(
                self.model.best_estimator_,
                X, y,
                n_repeats=10,
                random_state=self.random_state
            )

            importance_df = pd.DataFrame({
                'feature': X.columns,
                'importance': perm_importance.importances_mean,
                'std': perm_importance.importances_std
            }).sort_values('importance', ascending=False)

            return importance_df

    def evaluate_model(self, X_test, y_test):
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]

            # Calculate metrics
            results = {
                'confusion_matrix': confusion_matrix(y_test, y_pred),
                'classification_report': classification_report(y_test, y_pred),
                'accuracy': accuracy_score(y_test, y_pred)
            }

            # Calculate ROC curve and AUC
            fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
            results['roc_auc'] = auc(fpr, tpr)

            # Calculate Precision-Recall curve
            precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
            results['pr_auc'] = auc(recall, precision)

            # Calculate learning curves
            train_sizes, train_scores, test_scores = learning_curve(
                self.model.best_estimator_, X_test, y_test,
                cv=5, n_jobs=-1, train_sizes=np.linspace(0.1, 1.0, 10)
            )
            results['learning_curves'] = {
                'train_sizes': train_sizes,
                'train_scores': train_scores,
                'test_scores': test_scores
            }

            # Generate plots
            self.plot_model_evaluation(fpr, tpr, precision, recall, results)

            logging.info("Model evaluation completed")
            return results

    def plot_model_evaluation(self, fpr, tpr, precision, recall, results):
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))

            # Plot 1: ROC Curve
            axes[0, 0].plot(fpr, tpr, color='darkorange', lw=2,
                            label=f'ROC curve (AUC = {results["roc_auc"]:.2f})')
            axes[0, 0].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            axes[0, 0].set_title('Receiver Operating Characteristic (ROC) Curve')
            axes[0, 0].set_xlabel('False Positive Rate')
            axes[0, 0].set_ylabel('True Positive Rate')
            axes[0, 0].legend()

            # Plot 2: Precision-Recall Curve
            axes[0, 1].plot(recall, precision, color='blue', lw=2,
                            label=f'PR curve (AUC = {results["pr_auc"]:.2f})')
            axes[0, 1].set_title('Precision-Recall Curve')
            axes[0, 1].set_xlabel('Recall')
            axes[0, 1].set_ylabel('Precision')
            axes[0, 1].legend()

            # Plot 3: Learning Curves
            train_scores_mean = np.mean(results['learning_curves']['train_scores'], axis=1)
            train_scores_std = np.std(results['learning_curves']['train_scores'], axis=1)
            test_scores_mean = np.mean(results['learning_curves']['test_scores'], axis=1)
            test_scores_std = np.std(results['learning_curves']['test_scores'], axis=1)

            axes[1, 0].grid()
            axes[1, 0].fill_between(results['learning_curves']['train_sizes'],
                                    train_scores_mean - train_scores_std,
                                    train_scores_mean + train_scores_std, alpha=0.1,
                                    color="r")
            axes[1, 0].fill_between(results['learning_curves']['train_sizes'],
                                    test_scores_mean - test_scores_std,
                                    test_scores_mean + test_scores_std, alpha=0.1,
                                    color="g")
            axes[1, 0].plot(results['learning_curves']['train_sizes'], train_scores_mean, 'o-', color="r",
                            label="Training score")
            axes[1, 0].plot(results['learning_curves']['train_sizes'], test_scores_mean, 'o-', color="g",
                            label="Cross-validation score")
            axes[1, 0].set_title("Learning Curves")
            axes[1, 0].set_xlabel("Training examples")
            axes[1, 0].set_ylabel("Score")
            axes[1, 0].legend(loc="best")

            # Plot 4: Feature Importance
            importance_data = self.feature_importance.head(10)
            sns.barplot(x='importance', y='feature', data=importance_data, ax=axes[1, 1])
            axes[1, 1].set_title('Top 10 Feature Importance')

            plt.tight_layout()
            plt.show()

    def analyze_segment_churn(self, data):
            """
            Analyze churn patterns within customer segments
            """
            if self.customer_segments is None:
                self.perform_customer_segmentation(data)

            data['Segment'] = self.customer_segments
            segment_analysis = {}

            for segment in data['Segment'].unique():
                segment_data = data[data['Segment'] == segment]

                # Basic metrics
                segment_analysis[f'Segment_{segment}'] = {
                    'size': len(segment_data),
                    'churn_rate': segment_data['Churn'].mean(),
                    'avg_satisfaction': segment_data['SatisfactionScore'].mean(),
                    'avg_value': segment_data['AvgPurchaseValue'].mean(),
                    'avg_frequency': segment_data['PurchaseFrequency'].mean(),

                    # Additional metrics
                    'avg_engagement': segment_data['DigitalEngagementScore'].mean(),
                    'avg_products': segment_data['ProductsOwned'].mean(),
                    'support_calls_rate': segment_data['SupportCalls'].mean(),
                    'complaint_rate': segment_data['Complaints'].mean(),
                    'resolution_rate': segment_data['ComplaintResolutionRate'].mean()
                }

            # Convert to DataFrame for easier analysis
            segment_df = pd.DataFrame(segment_analysis).T

            # Generate segment profiles
            segment_df['risk_level'] = pd.qcut(segment_df['churn_rate'],
                                               q=3,
                                               labels=['Low', 'Medium', 'High'])

            # Plot segment analysis
            self.plot_segment_analysis(data)

            logging.info("Segment analysis completed")
            return segment_df

    def generate_customer_recommendations(self, customer_data):
            """
            Generate personalized recommendations based on customer profile
            """
            if not isinstance(customer_data, pd.DataFrame):
                raise ValueError("customer_data must be a pandas DataFrame")

            # Preprocess customer data
            processed_data = self.preprocess_data(customer_data)

            # Get predictions
            churn_prob = self.predict_churn_probability(processed_data)
            segment = self.kmeans.predict(self.scaler.transform(
                customer_data[['AvgPurchaseValue', 'PurchaseFrequency', 'ProductsOwned',
                               'UsageFrequency', 'DigitalEngagementScore', 'SatisfactionScore']]
            ))

            recommendations = []
            for idx, prob in enumerate(churn_prob):
                customer_recommendations = {
                    'customer_id': idx,
                    'churn_probability': prob,
                    'segment': segment[idx],
                    'risk_level': 'High' if prob > 0.7 else 'Medium' if prob > 0.4 else 'Low'
                }

                # Generate specific recommendations based on customer profile
                actions = []

                # High-risk recommendations
                if prob > 0.7:
                    actions.extend([
                        'Immediate personal contact by customer service',
                        'Offer personalized retention package',
                        'Conduct detailed satisfaction survey',
                        'Schedule account review meeting'
                    ])

                    # Add specific recommendations based on customer attributes
                    if customer_data.iloc[idx]['SatisfactionScore'] < 7:
                        actions.append('Priority support status for 30 days')
                    if customer_data.iloc[idx]['ProductsOwned'] < 2:
                        actions.append('Special cross-sell promotion')
                    if customer_data.iloc[idx]['UsageFrequency'] < 1:
                        actions.append('Personalized product training session')

                # Medium-risk recommendations
                elif prob > 0.4:
                    actions.extend([
                        'Send targeted promotional email',
                        'Offer product upgrade discount',
                        'Provide usage tips and best practices',
                        'Invite to customer feedback program'
                    ])

                    if customer_data.iloc[idx]['DigitalEngagementScore'] < 0.5:
                        actions.append('Mobile app activation promotion')
                    if customer_data.iloc[idx]['PurchaseFrequency'] < 2:
                        actions.append('Limited-time purchase incentive')

                # Low-risk recommendations
                else:
                    actions.extend([
                        'Regular newsletter enrollment',
                        'Loyalty program invitation',
                        'Product review request',
                        'Social media engagement campaign'
                    ])

                customer_recommendations['recommended_actions'] = actions
                recommendations.append(customer_recommendations)

            return pd.DataFrame(recommendations)

    def save_model(self, filepath):
            """
            Save the trained model and all necessary components
            """
            model_data = {
                'model': self.model,
                'label_encoder': self.label_encoder,
                'scaler': self.scaler,
                'poly_features': self.poly_features,
                'pca': self.pca,
                'kmeans': self.kmeans,
                'feature_importance': self.feature_importance,
                'feature_names': self.feature_names,
                'segment_profiles': self.segment_profiles if hasattr(self, 'segment_profiles') else None
            }

            joblib.dump(model_data, filepath)
            logging.info(f"Model saved to {filepath}")

    def load_model(self, filepath):
            """
            Load a previously saved model and all components
            """
            model_data = joblib.load(filepath)

            self.model = model_data['model']
            self.label_encoder = model_data['label_encoder']
            self.scaler = model_data['scaler']
            self.poly_features = model_data['poly_features']
            self.pca = model_data['pca']
            self.kmeans = model_data['kmeans']
            self.feature_importance = model_data['feature_importance']
            self.feature_names = model_data['feature_names']
            if model_data['segment_profiles'] is not None:
                self.segment_profiles = model_data['segment_profiles']

            logging.info(f"Model loaded from {filepath}")

    def generate_report(self, data, output_format='markdown'):
            """
            Generate a comprehensive analysis report
            """
            # Perform all analyses
            processed_data = self.preprocess_data(data)
            X = processed_data.drop('Churn', axis=1)
            y = processed_data['Churn']
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state
            )

            if self.model is None:
                self.train_model(X_train, y_train)

            evaluation_results = self.evaluate_model(X_test, y_test)
            segment_analysis = self.analyze_segment_churn(processed_data)
            recommendations = self.generate_customer_recommendations(data.head())

            # Create report
            report = {
                'summary': {
                    'total_customers': len(data),
                    'churn_rate': data['Churn'].mean(),
                    'model_accuracy': evaluation_results['accuracy'],
                    'roc_auc': evaluation_results['roc_auc'],
                    'num_segments': len(segment_analysis)
                },
                'model_performance': {
                    'classification_report': evaluation_results['classification_report'],
                    'confusion_matrix': evaluation_results['confusion_matrix'].tolist()
                },
                'segment_analysis': segment_analysis.to_dict(),
                'top_features': self.feature_importance.head(10).to_dict(),
                'sample_recommendations': recommendations.to_dict()
            }

            if output_format == 'json':
                return json.dumps(report, indent=2)
            else:
                # Generate markdown report
                md_report = f"""
        # Customer Churn Analysis Report

        ## Summary
        - Total Customers: {report['summary']['total_customers']:,}
        - Overall Churn Rate: {report['summary']['churn_rate']:.2%}
        - Model Accuracy: {report['summary']['model_accuracy']:.2%}
        - ROC AUC Score: {report['summary']['roc_auc']:.2f}
        - Number of Customer Segments: {report['summary']['num_segments']}

        ## Model Performance
        ```
        {report['model_performance']['classification_report']}
        ```

        ## Top Churn Predictors
        {self.feature_importance.head(10).to_markdown()}

        ## Segment Analysis
        {segment_analysis.to_markdown()}

        ## Sample Customer Recommendations
        {recommendations.head().to_markdown()}
        """
                return md_report

    def main(self):
        # Initialize the analyzer
        analyzer = ChurnAnalyzer()

        # Generate sample data
        data = analyzer.generate_mock_data(2000)

        # Preprocess data
        processed_data = analyzer.preprocess_data(data)

        # Split the data
        X = processed_data.drop('Churn', axis=1)
        y = processed_data['Churn']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train and evaluate model
        analyzer.train_model(X_train, y_train)
        results = analyzer.evaluate_model(X_test, y_test)

        # Perform segment analysis
        segment_analysis = analyzer.analyze_segment_churn(processed_data)
        print("\nSegment Analysis:")
        print(segment_analysis)

        # Generate recommendations for sample customers
        sample_customers = data.head()
        recommendations = analyzer.generate_customer_recommendations(sample_customers)
        print("\nSample Customer Recommendations:")
        print(recommendations)

        # Generate and save report
        report = analyzer.generate_report(data)
        with open('churn_analysis_report.md', 'w') as f:
            f.write(report)

        # Save the model
        analyzer.save_model('churn_model.joblib')