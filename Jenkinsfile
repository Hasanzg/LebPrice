pipeline {
    agent any

    triggers {
        githubPush()
    }

    environment {
        KUBECONFIG = "C:\\Users\\Khale\\.kube\\config"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/Hasanzg/LebPrice.git', credentialsId: 'github-creds'
            }
        }

        stage('Setup Minikube Docker') {
            steps {
                bat '''
                    for /f "tokens=*" %%i in ('minikube -p minikube docker-env --shell=cmd') do %%i
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                bat 'docker build -t backend:latest backend'
                bat 'docker build -t auth:latest auth'
                bat 'docker build -t frontend:latest frontend'
                bat 'docker build -t cart:latest cart'
            }
        }

        stage('Apply K8s Files') {
            steps {
                bat 'kubectl apply -f k8s'
            }
        }

        stage('Restart Backend') {
            steps {
                bat 'kubectl rollout restart deployment/backend'
            }
        }
    }
}
