#pragma once
#include <QString>
#include <QJsonObject>
#include <QProcess>
#include <windows.h>

class SystemMonitor
{
public:
    SystemMonitor();
    QJsonObject getSystemInfoJson();

private:
    double getCpuUsage();
    qint64 getMemoryTotal();
    qint64 getMemoryAvailable();
    qint64 getDiskTotal();
    qint64 getDiskFree();
    QString getOsInfo();
    QString getCpuInfo();
    QString getIpAddress();
    QString getUptime();

    static ULARGE_INTEGER prevIdle;
    static ULARGE_INTEGER prevKernel;
    static ULARGE_INTEGER prevUser;
    static bool initialized;
};