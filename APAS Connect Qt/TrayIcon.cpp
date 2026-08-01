#include "TrayIcon.h"
#include <QApplication>
#include <QAction>
#include <QPixmap>
#include <QPainter>

TrayIcon::TrayIcon(QObject *parent)
    : QSystemTrayIcon(parent)
{
    // Create a simple icon
    QPixmap pixmap(64, 64);
    pixmap.fill(Qt::transparent);
    QPainter painter(&pixmap);
    painter.setBrush(Qt::blue);
    painter.drawEllipse(4, 4, 56, 56);
    painter.setPen(Qt::white);
    painter.drawText(32, 32, "A");
    setIcon(QIcon(pixmap));

    setToolTip("APAS Connect");

    m_trayMenu = new QMenu();
    QAction *showAction = m_trayMenu->addAction("Show");
    connect(showAction, &QAction::triggered, []() {
        // Find main window
        foreach (QWidget *widget, QApplication::topLevelWidgets()) {
            if (widget->isWindow() && widget->windowTitle() == "APAS Connect") {
                widget->show();
                widget->raise();
                break;
            }
        }
    });

    QAction *quitAction = m_trayMenu->addAction("Quit");
    connect(quitAction, &QAction::triggered, QApplication::instance(), &QApplication::quit);

    setContextMenu(m_trayMenu);
    connect(this, &QSystemTrayIcon::activated, this, &TrayIcon::onTrayActivated);
}

void TrayIcon::showTrayIcon()
{
    show();
}

void TrayIcon::onTrayActivated(QSystemTrayIcon::ActivationReason reason)
{
    if (reason == QSystemTrayIcon::DoubleClick) {
        // Show window
        foreach (QWidget *widget, QApplication::topLevelWidgets()) {
            if (widget->isWindow() && widget->windowTitle() == "APAS Connect") {
                widget->show();
                widget->raise();
                break;
            }
        }
    }
}

void TrayIcon::showNotification(const QString &title, const QString &message)
{
    showMessage(title, message, QSystemTrayIcon::Information, 3000);
}