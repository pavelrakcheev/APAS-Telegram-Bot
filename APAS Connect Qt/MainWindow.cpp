#include "MainWindow.h"
#include <QWidget>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QJsonObject>
#include <QCloseEvent>
#include <QSystemTrayIcon>
#include <QApplication>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QMessageBox>
#include <QProcess>
#include <QDir>
#include <QStyle>
#include "TrayIcon.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), m_monitor(), m_darkTheme(true)
{
    setupUI();
    setWindowTitle("APAS Connect");
    resize(400, 350);
}

MainWindow::~MainWindow()
{
}

void MainWindow::setupUI()
{
    QWidget *centralWidget = new QWidget;
    setCentralWidget(centralWidget);

    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);

    // Buttons
    QHBoxLayout *buttonLayout = new QHBoxLayout();
    m_button = new QPushButton("Get System Info", this);
    m_button->setIcon(style()->standardIcon(QStyle::SP_ComputerIcon));
    connect(m_button, &QPushButton::clicked, this, &MainWindow::onGetInfoClicked);

    m_checkApiButton = new QPushButton("Check API & Models", this);
    m_checkApiButton->setIcon(style()->standardIcon(QStyle::SP_MessageBoxInformation));
    connect(m_checkApiButton, &QPushButton::clicked, this, &MainWindow::onCheckApiClicked);

    m_autoUpdateButton = new QPushButton("Start Auto Update", this);
    m_autoUpdateButton->setIcon(style()->standardIcon(QStyle::SP_MediaPlay));
    connect(m_autoUpdateButton, &QPushButton::clicked, this, &MainWindow::onAutoUpdateClicked);

    m_themeButton = new QPushButton("☀", this);
    connect(m_themeButton, &QPushButton::clicked, this, &MainWindow::onThemeToggleClicked);

    buttonLayout->addWidget(m_button);
    buttonLayout->addWidget(m_checkApiButton);
    buttonLayout->addWidget(m_autoUpdateButton);
    buttonLayout->addWidget(m_themeButton);
    mainLayout->addLayout(buttonLayout);

    // Info display
    QFormLayout *infoLayout = new QFormLayout();

    m_osLabel = new QLabel("Unknown", this);
    infoLayout->addRow("OS:", m_osLabel);

    m_uptimeLabel = new QLabel("0h 0m", this);
    infoLayout->addRow("Uptime:", m_uptimeLabel);

    m_ipLabel = new QLabel("0.0.0.0", this);
    infoLayout->addRow("IP:", m_ipLabel);

    m_cpuBar = new QProgressBar(this);
    m_cpuBar->setRange(0, 100);
    m_cpuBar->setFormat("%p%");
    infoLayout->addRow("CPU Usage:", m_cpuBar);

    m_ramBar = new QProgressBar(this);
    m_ramBar->setRange(0, 100);
    m_ramBar->setFormat("%p%");
    infoLayout->addRow("RAM Usage:", m_ramBar);

    m_diskBar = new QProgressBar(this);
    m_diskBar->setRange(0, 100);
    m_diskBar->setFormat("%v GB free");
    infoLayout->addRow("Disk Free:", m_diskBar);

    mainLayout->addLayout(infoLayout);

    // Apply dark theme QSS
    QString darkQss = R"(
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: Arial;
        }
        QPushButton {
            background-color: #404040;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 5px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #606060;
        }
        QLabel {
            font-size: 12px;
        }
        QProgressBar {
            border: 1px solid #555;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
    )";

    QString lightQss = R"(
        QWidget {
            background-color: #f0f0f0;
            color: #000000;
            font-family: Arial;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #aaa;
            border-radius: 5px;
            padding: 5px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        QLabel {
            font-size: 12px;
        }
        QProgressBar {
            border: 1px solid #aaa;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #2196F3;
        }
    )";

    setStyleSheet(m_darkTheme ? darkQss : lightQss);

    m_timer = new QTimer(this);
    connect(m_timer, &QTimer::timeout, this, &MainWindow::onGetInfoClicked);
}

void MainWindow::onGetInfoClicked()
{
    QJsonObject info = m_monitor.getSystemInfoJson();
    info = m_monitor.getSystemInfoJson(); // Second call for accurate CPU usage
    m_osLabel->setText(info["os"].toString());
    m_uptimeLabel->setText(info["uptime"].toString());
    m_ipLabel->setText(info["ip_address"].toString());
    m_cpuBar->setValue(info["cpu_percent"].toInt());
    m_ramBar->setValue(info["ram_percent"].toInt());
    m_diskBar->setMaximum(info["disk_total"].toInt());
    m_diskBar->setValue(info["disk_free"].toInt());
}

void MainWindow::onCheckApiClicked()
{
    // Check API connection
    QNetworkAccessManager *manager = new QNetworkAccessManager(this);
    QNetworkRequest request(QUrl("http://localhost:8080/system_info"));
    QNetworkReply *reply = manager->get(request);
    connect(reply, &QNetworkReply::finished, this, [this, reply, manager]() {
        bool apiOk = (reply->error() == QNetworkReply::NoError);
        QString apiStatus = apiOk ? "API работает" : "API не работает";

        // Check models
        QString modelOutput;
        QProcess *process1 = new QProcess(this);
        process1->setWorkingDirectory(QDir::currentPath() + "/../../.."); // To Bot root
        process1->start("python", QStringList() << "check_models.py");
        process1->waitForFinished(10000); // Wait up to 10s
        modelOutput += "Gemini:\n" + process1->readAllStandardOutput() + "\n" + process1->readAllStandardError() + "\n";

        QProcess *process2 = new QProcess(this);
        process2->setWorkingDirectory(QDir::currentPath() + "/../../..");
        process2->start("python", QStringList() << "check_vertexai.py");
        process2->waitForFinished(10000);
        modelOutput += "Vertex AI:\n" + process2->readAllStandardOutput() + "\n" + process2->readAllStandardError() + "\n";

        QProcess *process3 = new QProcess(this);
        process3->setWorkingDirectory(QDir::currentPath() + "/../../..");
        process3->start("python", QStringList() << "-c" << "try: import groq; import os; client = groq.Client(api_key=os.getenv('GROQ_API_KEY')); models = client.models.list(); print('Groq: OK, models:', len(models.data)) except Exception as e: print('Groq: Error -', str(e))");
        process3->waitForFinished(10000);
        modelOutput += "Groq:\n" + process3->readAllStandardOutput() + "\n" + process3->readAllStandardError() + "\n";

        QProcess *process4 = new QProcess(this);
        process4->setWorkingDirectory(QDir::currentPath() + "/../../..");
        process4->start("python", QStringList() << "-c" << "try: import requests; import os; headers = {'Authorization': f'Api-Key {os.getenv(\"YANDEX_API_KEY\")}', 'Content-Type': 'application/json'}; response = requests.get('https://llm.api.cloud.yandex.net/foundationModels/v1/models', headers=headers); if response.status_code == 200: print('Yandex: OK') else: print('Yandex: Error -', response.status_code) except Exception as e: print('Yandex: Error -', str(e))");
        process4->waitForFinished(10000);
        modelOutput += "Yandex:\n" + process4->readAllStandardOutput() + "\n" + process4->readAllStandardError();

        QMessageBox::information(this, "Check Results", apiStatus + "\n\n" + modelOutput);
        reply->deleteLater();
        manager->deleteLater();
        process1->deleteLater();
        process2->deleteLater();
        process3->deleteLater();
        process4->deleteLater();
    });
}

void MainWindow::onAutoUpdateClicked()
{
    if (m_timer->isActive()) {
        m_timer->stop();
        m_autoUpdateButton->setText("Start Auto Update");
        m_autoUpdateButton->setIcon(style()->standardIcon(QStyle::SP_MediaPlay));
    } else {
        m_timer->start(5000); // Update every 5 seconds
        m_autoUpdateButton->setText("Stop Auto Update");
        m_autoUpdateButton->setIcon(style()->standardIcon(QStyle::SP_MediaStop));
        onGetInfoClicked(); // Update immediately
    }
}

void MainWindow::onThemeToggleClicked()
{
    m_darkTheme = !m_darkTheme;
    QString darkQss = R"(
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: Arial;
        }
        QPushButton {
            background-color: #404040;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 5px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #606060;
        }
        QLabel {
            font-size: 12px;
        }
        QProgressBar {
            border: 1px solid #555;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
    )";

    QString lightQss = R"(
        QWidget {
            background-color: #f0f0f0;
            color: #000000;
            font-family: Arial;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #aaa;
            border-radius: 5px;
            padding: 5px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        QLabel {
            font-size: 12px;
        }
        QProgressBar {
            border: 1px solid #aaa;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #2196F3;
        }
    )";

    setStyleSheet(m_darkTheme ? darkQss : lightQss);
    m_themeButton->setText(m_darkTheme ? "☀" : "🌙");
}

void MainWindow::closeEvent(QCloseEvent *event)
{
    // Stop timer if active
    if (m_timer->isActive()) {
        m_timer->stop();
    }
    // Instead of closing, hide to tray
    hide();
    TrayIcon *tray = qobject_cast<TrayIcon*>(parent());
    if (tray) {
        tray->showNotification("APAS Connect", "Program is running in the background");
    }
    event->ignore(); // Don't close
}