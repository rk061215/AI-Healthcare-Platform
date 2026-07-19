"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm, type UseFormReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { authService } from "@/services/auth";
import { useAuthStore } from "@/lib/store/auth-store";
import { Loader2, Stethoscope, User } from "lucide-react";

const PASSWORD_RULES = {
  minLength: 8,
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  number: /[0-9]/,
  special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/,
};

const patientSchema = z
  .object({
    full_name: z.string().min(1, "Full name is required").max(255),
    email: z.string().email("Invalid email address"),
    phone: z
      .string()
      .regex(/^\+?[1-9]\d{1,14}$/, "Invalid phone number (E.164 format)")
      .optional()
      .or(z.literal("")),
    date_of_birth: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/, "Use format YYYY-MM-DD")
      .optional()
      .or(z.literal("")),
    gender: z.enum(["male", "female", "other", "prefer_not_to_say"]).optional().or(z.literal("")),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(PASSWORD_RULES.uppercase, "Must contain an uppercase letter")
      .regex(PASSWORD_RULES.lowercase, "Must contain a lowercase letter")
      .regex(PASSWORD_RULES.number, "Must contain a number")
      .regex(PASSWORD_RULES.special, "Must contain a special character"),
    confirm_password: z.string().min(1, "Please confirm your password"),
    terms_accepted: z.boolean().refine((v) => v === true, "You must accept the terms"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

const doctorSchema = z
  .object({
    full_name: z.string().min(1, "Full name is required").max(255),
    email: z.string().email("Invalid email address"),
    phone: z
      .string()
      .regex(/^\+?[1-9]\d{1,14}$/, "Invalid phone number (E.164 format)")
      .optional()
      .or(z.literal("")),
    license_number: z.string().optional().or(z.literal("")),
    hospital_name: z.string().optional().or(z.literal("")),
    specialization: z.string().optional().or(z.literal("")),
    years_of_experience: z
      .string()
      .optional()
      .refine(
        (val) => !val || (!isNaN(Number(val)) && Number(val) >= 0 && Number(val) <= 70),
        "Must be between 0 and 70",
      ),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(PASSWORD_RULES.uppercase, "Must contain an uppercase letter")
      .regex(PASSWORD_RULES.lowercase, "Must contain a lowercase letter")
      .regex(PASSWORD_RULES.number, "Must contain a number")
      .regex(PASSWORD_RULES.special, "Must contain a special character"),
    confirm_password: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type PatientForm = z.infer<typeof patientSchema>;
type DoctorForm = z.infer<typeof doctorSchema>;

type Step = "role" | "form";

export default function RegisterPage() {
  const [role, setRole] = useState<"patient" | "doctor">("patient");
  const [step, setStep] = useState<Step>("role");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const patientForm = useForm<PatientForm>({
    resolver: zodResolver(patientSchema),
    defaultValues: { terms_accepted: false },
  });

  const doctorForm = useForm<DoctorForm>({
    resolver: zodResolver(doctorSchema),
  });

  const currentForm = role === "patient" ? patientForm : doctorForm;
  const {
    register,
    handleSubmit,
    formState: { errors },
  }: any = currentForm;

  const selectRole = (selected: "patient" | "doctor") => {
    setRole(selected);
    setStep("form");
  };

  const onSubmit = async (data: PatientForm | DoctorForm) => {
    setLoading(true);
    try {
      let response;
      if (role === "patient") {
        const pData = data as PatientForm;
        response = await authService.registerPatient({
          email: pData.email,
          password: pData.password,
          confirm_password: pData.confirm_password,
          full_name: pData.full_name,
          phone: pData.phone || undefined,
          date_of_birth: pData.date_of_birth || undefined,
          gender: pData.gender || undefined,
          terms_accepted: true,
        });
      } else {
        const dData = data as DoctorForm;
        response = await authService.registerDoctor({
          email: dData.email,
          password: dData.password,
          confirm_password: dData.confirm_password,
          full_name: dData.full_name,
          phone: dData.phone || undefined,
          license_number: dData.license_number || undefined,
          hospital_name: dData.hospital_name || undefined,
          specialization: dData.specialization || undefined,
          years_of_experience: dData.years_of_experience
            ? Number(dData.years_of_experience)
            : undefined,
        });
      }

      setAuth(response.user, response.access_token, response.refresh_token);
      toast.success("Account created successfully");

      const dashboard = role === "patient" ? "/patient/dashboard" : "/doctor/dashboard";
      router.push(dashboard);
    } catch (error: any) {
      console.error("=== REGISTRATION ERROR ===", {
        message: error?.message,
        responseStatus: error?.response?.status,
        responseData: JSON.stringify(error?.response?.data),
        responseHeaders: error?.response?.headers,
        isAxiosError: error?.isAxiosError,
        code: error?.code,
        stack: error?.stack,
      });
      const message = error?.response?.data?.error || error?.response?.data?.detail || "Registration failed";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  if (step === "role") {
    return (
      <Card className="w-full">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Create Account</CardTitle>
          <CardDescription>Choose your account type to get started</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <button
            type="button"
            onClick={() => selectRole("patient")}
            className="flex w-full items-center gap-4 rounded-lg border p-4 text-left transition-colors hover:bg-accent"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <User className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="font-semibold">Patient</p>
              <p className="text-sm text-muted-foreground">
                Manage your medications, reports, and appointments
              </p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => selectRole("doctor")}
            className="flex w-full items-center gap-4 rounded-lg border p-4 text-left transition-colors hover:bg-accent"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <Stethoscope className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="font-semibold">Doctor</p>
              <p className="text-sm text-muted-foreground">
                Monitor patients, review reports, and manage alerts
              </p>
            </div>
          </button>
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="text-center">
        <div className="mb-2 flex items-center justify-center gap-2">
          {role === "patient" ? (
            <User className="h-5 w-5 text-primary" />
          ) : (
            <Stethoscope className="h-5 w-5 text-primary" />
          )}
          <CardTitle className="text-xl">
            {role === "patient" ? "Patient Registration" : "Doctor Registration"}
          </CardTitle>
        </div>
        <CardDescription>
          Fill in your details to create your account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name</Label>
            <Input id="full_name" placeholder="John Doe" {...register("full_name")} />
            {errors.full_name && (
              <p className="text-xs text-destructive">{errors.full_name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="you@example.com" {...register("email")} />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number (optional)</Label>
            <Input id="phone" type="tel" placeholder="+1234567890" {...register("phone")} />
            {errors.phone && (
              <p className="text-xs text-destructive">{errors.phone.message}</p>
            )}
          </div>

          {role === "patient" && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date_of_birth">Date of Birth (optional)</Label>
                  <Input id="date_of_birth" placeholder="YYYY-MM-DD" {...patientForm.register("date_of_birth")} />
                  {patientForm.formState.errors.date_of_birth && (
                    <p className="text-xs text-destructive">
                      {patientForm.formState.errors.date_of_birth.message}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="gender">Gender (optional)</Label>
                  <select
                    id="gender"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    {...patientForm.register("gender")}
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                    <option value="prefer_not_to_say">Prefer not to say</option>
                  </select>
                  {patientForm.formState.errors.gender && (
                    <p className="text-xs text-destructive">
                      {patientForm.formState.errors.gender.message}
                    </p>
                  )}
                </div>
              </div>
            </>
          )}

          {role === "doctor" && (
            <>
              <div className="space-y-2">
                <Label htmlFor="specialization">Specialization (optional)</Label>
                <Input
                  id="specialization"
                  placeholder="Cardiology"
                  {...doctorForm.register("specialization")}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="license_number">License Number (optional)</Label>
                  <Input
                    id="license_number"
                    placeholder="LIC-12345"
                    {...doctorForm.register("license_number")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="hospital_name">Hospital (optional)</Label>
                  <Input
                    id="hospital_name"
                    placeholder="City Hospital"
                    {...doctorForm.register("hospital_name")}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="years_of_experience">Years of Experience (optional)</Label>
                <Input
                  id="years_of_experience"
                  type="number"
                  placeholder="10"
                  {...doctorForm.register("years_of_experience")}
                />
                {doctorForm.formState.errors.years_of_experience && (
                  <p className="text-xs text-destructive">
                    {doctorForm.formState.errors.years_of_experience.message}
                  </p>
                )}
              </div>
            </>
          )}

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="At least 8 characters"
              {...register("password")}
            />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Must contain: uppercase, lowercase, number, and special character
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">Confirm Password</Label>
            <Input
              id="confirm_password"
              type="password"
              placeholder="Repeat your password"
              {...register("confirm_password")}
            />
            {errors.confirm_password && (
              <p className="text-xs text-destructive">{errors.confirm_password.message}</p>
            )}
          </div>

          {role === "patient" && (
            <div className="flex items-start gap-2">
              <input
                id="terms_accepted"
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                {...patientForm.register("terms_accepted")}
              />
              <Label htmlFor="terms_accepted" className="text-sm font-normal cursor-pointer">
                I accept the terms and conditions and privacy policy
              </Label>
            </div>
          )}
          {patientForm.formState.errors.terms_accepted && (
            <p className="text-xs text-destructive">
              {patientForm.formState.errors.terms_accepted.message}
            </p>
          )}

          <div className="flex gap-3">
            <Button
              type="button"
              variant="outline"
              className="flex-1"
              onClick={() => setStep("role")}
            >
              Back
            </Button>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </Button>
          </div>
        </form>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
