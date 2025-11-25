pipeline {
    agent any

    triggers {
        githubPush()   // Auto-run when code changes on GitHub
    }

    environment {
        KUBECONFIG = "$HOME/.kube/config"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', 
                    url: 'https://github.com/Hasanzg/LebPrice.git',
                    credentialsId: '2'
            }
        }


        stage('Setup Minikube Docker') {
            steps {
                sh 'eval $(minikube -p minikube docker-env)'
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'docker build -t backend:latest ./backend'
                sh 'docker build -t auth:latest ./auth'
                sh 'docker build -t frontend:latest ./frontend'
                sh 'docker build -t cart:latest ./cart'
            }
        }

        stage('Apply K8s Files') {
            steps {
                sh 'kubectl apply -f k8s/'
            }
        }

        stage('Restart Backend') {
            steps {
                sh 'kubectl rollout restart deployment/backend'
            }
        }
    }
}
