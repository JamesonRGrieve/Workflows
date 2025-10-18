using SampleApp;
using Xunit;

namespace SampleApp.Tests;

public class CalculatorTests
{
    [Fact]
    public void Add_ReturnsSum()
    {
        Assert.Equal(5, Calculator.Add(2, 3));
    }

    [Fact]
    public void Subtract_ReturnsDifference()
    {
        Assert.Equal(3, Calculator.Subtract(5, 2));
    }

    [Fact]
    public void Multiply_ReturnsProduct()
    {
        Assert.Equal(24, Calculator.Multiply(4, 6));
    }

    [Theory]
    [InlineData(10, 2, 5)]
    [InlineData(7, -1, -7)]
    public void Divide_ReturnsQuotient(int lhs, int rhs, double expected)
    {
        Assert.Equal(expected, Calculator.Divide(lhs, rhs));
    }

    [Fact]
    public void Divide_ThrowsWhenDividingByZero()
    {
        Assert.Throws<DivideByZeroException>(() => Calculator.Divide(4, 0));
    }
}
