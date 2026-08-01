#pragma once
#include <QTcpServer>
#include <QTcpSocket>
#include <QJsonObject>
#include <QJsonDocument>
#include "SystemMonitor.h"

class HttpServer : public QTcpServer
{
    Q_OBJECT

public:
    HttpServer(QObject *parent = nullptr);
    void startServer();

protected:
    void incomingConnection(qintptr socketDescriptor) override;

private:
    SystemMonitor m_monitor;
    void handleRequest(QTcpSocket *socket, const QByteArray &request);
};