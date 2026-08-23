pipeline {
    agent any

    environment {
        REGISTRY   = 'docker.io/christianobij'
        IMAGE_NAME = 'cloudshift-app'
        IMAGE_TAG  = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : env.BUILD_NUMBER}"
        NAMESPACE  = 'cloudshift'
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'k8s-production',
                    url: 'https://github.com/christianobi1/cloudshift-automation-toolkit.git'
            }
        }

        stage('Build & Test') {
            steps {
                sh 'pip install --break-system-packages -r requirements.txt pytest'
                sh 'pytest test_backup.py test_app.py -v'
            }
        }

        stage('Docker Build & Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker build -t $REGISTRY/$IMAGE_NAME:$IMAGE_TAG .
                        docker push $REGISTRY/$IMAGE_NAME:$IMAGE_TAG
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(
                    credentialsId: 'kubeconfig-cloudshift',
                    variable: 'KUBECONFIG'
                )]) {
                    sh '''
                        kubectl apply -k k8s/
                        kubectl set image deployment/cloudshift-web \
                            web=$REGISTRY/$IMAGE_NAME:$IMAGE_TAG \
                            -n $NAMESPACE
                        kubectl rollout status deployment/cloudshift-web \
                            -n $NAMESPACE --timeout=120s
                    '''
                }
            }
        }
    }

    post {
        failure {
            echo 'Deploy failed — rolling back to the previous known-good revision.'

            withCredentials([file(
                credentialsId: 'kubeconfig-cloudshift',
                variable: 'KUBECONFIG'
            )]) {
                sh 'kubectl rollout undo deployment/cloudshift-web -n $NAMESPACE || true'
            }
        }

        always {
            sh 'docker logout || true'
        }
    }
}
