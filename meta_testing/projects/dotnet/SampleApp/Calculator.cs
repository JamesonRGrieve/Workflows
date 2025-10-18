namespace SampleApp;

public static class Calculator
{
    public static int Add(int lhs, int rhs) => lhs + rhs;

    public static int Subtract(int lhs, int rhs) => lhs - rhs;

    public static int Multiply(int lhs, int rhs) => lhs * rhs;

    public static double Divide(int lhs, int rhs)
    {
        if (rhs == 0)
        {
            throw new DivideByZeroException("Division by zero is undefined");
        }

        return (double)lhs / rhs;
    }
}
