#include "HttpServer.h"
#include <QTcpSocket>
#include <QJsonObject>
#include <QJsonDocument>

HttpServer::HttpServer(QObject *parent)
    : QTcpServer(parent)
{
}

void HttpServer::startServer()
{
    if (listen(QHostAddress::LocalHost, 5000)) {
        qDebug() << "HTTP Server started on http://127.0.0.1:5000";
    } else {
        qDebug() << "Failed to start HTTP server";
    }
}

void HttpServer::incomingConnection(qintptr socketDescriptor)
{
    QTcpSocket *socket = new QTcpSocket(this);
    socket->setSocketDescriptor(socketDescriptor);

    connect(socket, &QTcpSocket::readyRead, this, [this, socket]() {
        QByteArray request = socket->readAll();
        handleRequest(socket, request);
    });

    connect(socket, &QTcpSocket::disconnected, socket, &QTcpSocket::deleteLater);
}

void HttpServer::handleRequest(QTcpSocket *socket, const QByteArray &request)
{
    QString reqStr = QString::fromUtf8(request);
    if (reqStr.contains("GET /system_info")) {
        QJsonObject json = m_monitor.getSystemInfoJson();
        QJsonDocument doc(json);
        QByteArray response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + doc.toJson();
        socket->write(response);
    } else {
        QByteArray response = "HTTP/1.1 404 Not Found\r\n\r\n";
        socket->write(response);
    }
    socket->disconnectFromHost();
}