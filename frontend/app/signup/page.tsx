'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import Link from 'next/link';
import { Checkbox } from '@/components/ui/checkbox';

const signupSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email address'),
  organization_name: z.string().min(1, 'Organization name is required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
  terms_accepted: z.boolean().refine((val) => val === true, 'You must accept the terms'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type SignupFormValues = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      terms_accepted: false,
    }
  });

  const onSubmit = async (data: SignupFormValues) => {
    setIsLoading(true);
    try {
      // API expects: email, password, first_name, last_name, organization_name, terms_accepted
      const payload = {
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        organization_name: data.organization_name,
        terms_accepted: data.terms_accepted,
      };
      
      const response = await api.post('/auth/signup/', payload);
      
      // Assuming signup returns user and org, but maybe not token immediately if verification is needed.
      // If it returns tokens, we login. If not, we redirect to login or verify page.
      // Based on analysis: Response Data: user (User Obj), organization (Org Obj), token (JWT)
      
      if (response.data.access) {
         const { access, refresh, user } = response.data;
         login(access, refresh, user);
         toast.success('Account created successfully');
      } else {
         toast.success('Account created! Please check your email to verify.');
         // Redirect to login or a specific success page
         window.location.href = '/login';
      }

    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.detail || 'Failed to create account');
      if (error.response?.data) {
          // Handle field errors if returned in a specific format
          Object.keys(error.response.data).forEach((key) => {
              if (key !== 'detail') {
                  toast.error(`${key}: ${error.response.data[key]}`);
              }
          });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Create your account</CardTitle>
          <CardDescription>
            Get started with your organization's email campaigns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name">First Name</Label>
                <Input id="first_name" {...register('first_name')} />
                {errors.first_name && <p className="text-sm text-red-500">{errors.first_name.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Last Name</Label>
                <Input id="last_name" {...register('last_name')} />
                {errors.last_name && <p className="text-sm text-red-500">{errors.last_name.message}</p>}
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="organization_name">Organization Name</Label>
              <Input id="organization_name" {...register('organization_name')} />
              {errors.organization_name && <p className="text-sm text-red-500">{errors.organization_name.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register('email')} />
              {errors.email && <p className="text-sm text-red-500">{errors.email.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" {...register('password')} />
              {errors.password && <p className="text-sm text-red-500">{errors.password.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input id="confirmPassword" type="password" {...register('confirmPassword')} />
              {errors.confirmPassword && <p className="text-sm text-red-500">{errors.confirmPassword.message}</p>}
            </div>

            <div className="flex items-center space-x-2">
              <input 
                type="checkbox" 
                id="terms" 
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                {...register('terms_accepted')}
              />
              <Label htmlFor="terms" className="text-sm font-normal">
                I accept the <Link href="/terms" className="text-primary hover:underline">terms and conditions</Link>
              </Label>
            </div>
            {errors.terms_accepted && <p className="text-sm text-red-500">{errors.terms_accepted.message}</p>}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Creating account...' : 'Create Account'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-gray-500">
            Already have an account?{' '}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
