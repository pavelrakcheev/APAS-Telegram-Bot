#include <QApplication>
#include <QSystemTrayIcon>
#include <QMenu>
#include <QAction>
#include "MainWindow.h"
#include "TrayIcon.h"
#include "HttpServer.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    // Set application properties
    app.setApplicationName("APAS Connect");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("APAS");

    // Start HTTP server
    HttpServer server;
    server.startServer();

    // Create main window
    MainWindow window;
    window.show();

    // Create tray icon
    TrayIcon tray;
    tray.showTrayIcon();
    tray.showNotification("APAS Connect", "Application started and running in system tray");

    return app.exec();
}