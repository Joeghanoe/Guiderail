public sealed class HealthFunctions(IPartnerService partner)
{
    [Function(nameof(Health))]
    public async Task<IActionResult> Health(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequest req,
        CancellationToken ct)
    {
        var result = await partner.HealthAsync(ct);
        return new ObjectResult(result) { StatusCode = result.IsHealthy ? 200 : 503 };
    }
}
