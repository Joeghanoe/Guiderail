public sealed class CustomersFunction(CustomerService service, ILogger<CustomersFunction> logger)
{
    public async Task<HttpResponseData> Run(HttpRequestData request, CancellationToken ct)
    {
        try
        {
            var items = await service.GetAllAsync(ct);
            return await request.OkAsync(items);
        }
        catch (StoreException ex)
        {
            logger.LogError(ex, "Store error fetching customers");
            return await request.ServiceUnavailableAsync();
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unhandled error fetching customers");
            return await request.ServiceUnavailableAsync();
        }
    }
}
