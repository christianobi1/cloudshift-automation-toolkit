pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'christianobij/cloudshift-app'
        K8S_NAMESPACE = 'cloudshift'
        K8S_DEPLOYMENT = 'cloudshift-web'
    }

    stages {

        stage('Build & Test') {
            steps {
                sh '''
                    python3 -m pip install --user pytest
                    python3 -m pytest test_backup.py
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build \
                      -t ${DOCKER_IMAGE}:${BUILD_NUMBER} \
                      -t ${DOCKER_IMAGE}:latest \
                      .
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {
                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login \
                          -u "$DOCKER_USERNAME" \
                          --password-stdin

                        docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker push ${DOCKER_IMAGE}:latest

                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    kubectl -n ${K8S_NAMESPACE} set image \
                      deployment/${K8S_DEPLOYMENT} \
                      web=${DOCKER_IMAGE}:${BUILD_NUMBER}

                    kubectl -n ${K8S_NAMESPACE} rollout status \
                      deployment/${K8S_DEPLOYMENT} \
                      --timeout=180s
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    echo "=== Deployment ==="
                    kubectl get deployment ${K8S_DEPLOYMENT} -n ${K8S_NAMESPACE}

                    echo "=== Pods ==="
                    kubectl get pods -n ${K8S_NAMESPACE}

                    echo "=== Service ==="
                    kubectl get svc ${K8S_DEPLOYMENT} -n ${K8S_NAMESPACE}
                '''
            }
        }
    }

    post {
        success {
            echo 'CloudShift CI/CD pipeline completed successfully!'
        }

        failure {
            echo 'CloudShift CI/CD pipeline failed.'
        }
    }
}
