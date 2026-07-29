pipeline {
    agent any

    stages {
        stage('Build & Test') {
            steps {
                sh 'pip install pytest'
                sh 'pytest test_backup.py'
            }
        }
    }
}
