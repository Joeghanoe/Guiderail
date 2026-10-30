namespace Contoso.Orders;

public sealed class OrderWorker(IOrderClient client) : BackgroundService
{
    protected override Task ExecuteAsync(CancellationToken stoppingToken) =>
        client.ProcessPendingAsync(stoppingToken);
}
