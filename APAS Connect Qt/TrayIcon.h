#pragma once
#include <QSystemTrayIcon>
#include <QMenu>

class TrayIcon : public QSystemTrayIcon
{
    Q_OBJECT

public:
    TrayIcon(QObject *parent = nullptr);
    void showTrayIcon();
    void showNotification(const QString &title, const QString &message);

private slots:
    void onTrayActivated(QSystemTrayIcon::ActivationReason reason);

private:
    QMenu *m_trayMenu;
};