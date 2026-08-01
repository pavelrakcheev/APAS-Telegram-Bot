#include "SystemMonitor.h"
#include <QProcess>
#include <QJsonObject>
#include <QHostInfo>
#include <QNetworkInterface>
#include <QSysInfo>
#include <windows.h>

ULARGE_INTEGER SystemMonitor::prevIdle = {0};
ULARGE_INTEGER SystemMonitor::prevKernel = {0};
ULARGE_INTEGER SystemMonitor::prevUser = {0};
bool SystemMonitor::initialized = false;

SystemMonitor::SystemMonitor()
{
}

QJsonObject SystemMonitor::getSystemInfoJson()
{
    QJsonObject json;
    json["os"] = getOsInfo();
    json["cpu"] = getCpuInfo();
    json["ram_total"] = getMemoryTotal() / (1024 * 1024 * 1024); // GB
    json["disk_total"] = getDiskTotal() / (1024 * 1024 * 1024); // GB
    json["cpu_percent"] = getCpuUsage();
    json["ram_percent"] = (1.0 - (double)getMemoryAvailable() / getMemoryTotal()) * 100;
    json["disk_free"] = getDiskFree() / (1024 * 1024 * 1024); // GB
    json["ip_address"] = getIpAddress();
    json["uptime"] = getUptime();
    return json;
}

double SystemMonitor::getCpuUsage()
{
    FILETIME idleTime, kernelTime, userTime;
    GetSystemTimes(&idleTime, &kernelTime, &userTime);

    ULARGE_INTEGER idle, kernel, user;
    idle.LowPart = idleTime.dwLowDateTime;
    idle.HighPart = idleTime.dwHighDateTime;
    kernel.LowPart = kernelTime.dwLowDateTime;
    kernel.HighPart = kernelTime.dwHighDateTime;
    user.LowPart = userTime.dwLowDateTime;
    user.HighPart = userTime.dwHighDateTime;

    if (!initialized) {
        prevIdle = idle;
        prevKernel = kernel;
        prevUser = user;
        initialized = true;
        return 0.0;
    }

    ULARGE_INTEGER idleDiff, kernelDiff, userDiff;
    idleDiff.QuadPart = idle.QuadPart - prevIdle.QuadPart;
    kernelDiff.QuadPart = kernel.QuadPart - prevKernel.QuadPart;
    userDiff.QuadPart = user.QuadPart - prevUser.QuadPart;

    double cpuUsage = 100.0 * (kernelDiff.QuadPart - idleDiff.QuadPart) / (kernelDiff.QuadPart + userDiff.QuadPart);

    prevIdle = idle;
    prevKernel = kernel;
    prevUser = user;

    return cpuUsage;
}

qint64 SystemMonitor::getMemoryTotal()
{
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&memInfo);
    return memInfo.ullTotalPhys;
}

qint64 SystemMonitor::getMemoryAvailable()
{
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&memInfo);
    return memInfo.ullAvailPhys;
}

qint64 SystemMonitor::getDiskTotal()
{
    ULARGE_INTEGER total;
    GetDiskFreeSpaceEx(L"C:\\", NULL, &total, NULL);
    return total.QuadPart;
}

qint64 SystemMonitor::getDiskFree()
{
    ULARGE_INTEGER free;
    GetDiskFreeSpaceEx(L"C:\\", NULL, NULL, &free);
    return free.QuadPart;
}

QString SystemMonitor::getOsInfo()
{
    return QSysInfo::productType() + " " + QSysInfo::productVersion();
}

QString SystemMonitor::getCpuInfo()
{
    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    return QString("x64 Processor"); // Simplified
}

QString SystemMonitor::getIpAddress()
{
    QList<QHostAddress> addresses = QNetworkInterface::allAddresses();
    for (const QHostAddress &address : addresses) {
        if (address.protocol() == QAbstractSocket::IPv4Protocol && address != QHostAddress::LocalHost) {
            return address.toString();
        }
    }
    return "Unknown";
}

QString SystemMonitor::getUptime()
{
    ULONGLONG uptime = GetTickCount64() / 1000; // seconds
    int hours = uptime / 3600;
    int minutes = (uptime % 3600) / 60;
    return QString("%1 ч %2 мин").arg(hours).arg(minutes);
}