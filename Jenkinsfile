pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'christianobij/cloudshift-app'
        DOCKER_TAG = "${BUILD_NUMBER}"
    }

    stages {

        stage('Build & Test') {
            steps {
                sh 'python3 -m pip install --user pytest'
                sh 'python3 -m pytest test_app.py'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $DOCKER_IMAGE:$DOCKER_TAG .'
                sh 'docker tag $DOCKER_IMAGE:$DOCKER_TAG $DOCKER_IMAGE:latest'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {
                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
                        docker push $DOCKER_IMAGE:$DOCKER_TAG
                        docker push $DOCKER_IMAGE:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    kubectl -n cloudshift set image deployment/cloudshift-web \
                    web=$DOCKER_IMAGE:$DOCKER_TAG

                    kubectl -n cloudshift rollout status deployment/cloudshift-web --timeout=120s
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    kubectl get pods -n cloudshift
                    kubectl get deployment -n cloudshift
                    kubectl get service -n cloudshift
                '''
            }
        }
    }
}