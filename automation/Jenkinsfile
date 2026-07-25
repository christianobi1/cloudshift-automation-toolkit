pipeline {
    agent any

    stages {

        stage('Build & Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    pip install pytest
                    pytest test_backup.py
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh 'python3 run_all.py'
            }
        }

    }
}
