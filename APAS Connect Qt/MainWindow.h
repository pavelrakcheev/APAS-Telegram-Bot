#pragma once
#include <QMainWindow>
#include <QPushButton>
#include <QLabel>
#include <QProgressBar>
#include <QTimer>
#include <QVBoxLayout>
#include <QMouseEvent>
#include "SystemMonitor.h"

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

protected:
    void closeEvent(QCloseEvent *event) override;

private slots:
    void onGetInfoClicked();
    void onCheckApiClicked();
    void onAutoUpdateClicked();
    void onThemeToggleClicked();

private:
    void setupUI();

    QPushButton *m_button;
    QPushButton *m_checkApiButton;
    QPushButton *m_autoUpdateButton;
    QPushButton *m_themeButton;
    QLabel *m_osLabel;
    QLabel *m_uptimeLabel;
    QLabel *m_ipLabel;
    QProgressBar *m_cpuBar;
    QProgressBar *m_ramBar;
    QProgressBar *m_diskBar;
    QTimer *m_timer;
    bool m_darkTheme;
    SystemMonitor m_monitor;
};